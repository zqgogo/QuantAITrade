# 任务状态管理与系统健壮性设计

## 一、设计目标

设计一套完整的任务状态管理机制,确保系统在随时停止、暂停、重启等场景下,能够:

1. **状态持久化**: 所有关键任务状态保存到数据库,重启后可恢复
2. **幂等性保证**: 任务重复执行不会造成数据冲突或业务逻辑错误
3. **断点续传**: 中断的任务可以从上次位置继续执行
4. **数据一致性**: 确保订单、持仓、交易记录等核心数据的完整性
5. **优雅关闭**: 系统停止时能够安全保存所有运行状态

## 二、核心问题分析

### 2.1 当前系统的状态管理现状

**已有机制**:
- 使用 APScheduler 管理定时任务
- 订单、持仓、交易记录等核心数据持久化到 SQLite
- 通过信号处理器(SIGINT/SIGTERM)实现优雅关闭
- 各组件(调度器、交易执行器、交易所连接器)有基本的启动/停止逻辑

**存在的不足**:
- 缺少统一的系统状态记录表
- 任务执行状态未持久化(队列中的信号丢失)
- 数据获取任务无断点续传机制
- 没有任务执行日志追踪
- 重启后无法判断上次运行状态
- 多次启动可能导致任务重复执行

### 2.2 需要管理的关键状态

| 状态类别 | 具体内容 | 当前持久化情况 | 重启影响 |
|---------|---------|--------------|---------|
| **系统运行状态** | 运行模式、启动时间、上次关闭时间、关闭原因 | ❌ 未保存 | 无法判断上次运行情况 |
| **任务调度状态** | 每个定时任务的上次执行时间、下次执行时间 | ⚠️ APScheduler 内存管理 | 重启后重新计算执行时间 |
| **数据获取进度** | 每个交易对的最新数据时间戳、是否完整 | ✅ 通过 kline_data 表隐式管理 | 可恢复,但无明确标记 |
| **交易信号队列** | 待处理的策略信号 | ❌ 仅存在内存队列 | 重启丢失所有未处理信号 |
| **订单执行状态** | 已提交但未完成的订单 | ✅ 保存在 trade_records | 可查询但需手动同步 |
| **持仓监控状态** | 开仓持仓、止损价、浮动盈亏 | ✅ 保存在 positions 表 | 可恢复并继续监控 |
| **AI分析任务** | 是否已生成当日分析、分析结果 | ✅ 保存在 ai_analysis_log | 可判断是否需要重新执行 |

## 三、设计方案

### 3.1 系统状态持久化

#### 3.1.1 新增数据表: system_state

```
字段说明:
- id: 主键
- instance_id: 系统实例唯一标识(UUID)
- run_mode: 运行模式(manual/auto/hybrid)
- status: 系统状态(running/stopped/paused/crashed)
- start_time: 启动时间戳
- stop_time: 停止时间戳
- stop_reason: 停止原因(manual/signal/error/crash)
- pid: 进程ID
- heartbeat_time: 最后心跳时间
- config_snapshot: 启动时的配置快照(JSON)
- created_at: 记录创建时间
```

**功能说明**:
- 每次系统启动时插入新记录
- 运行期间定期更新心跳时间(每30秒)
- 关闭时更新 status 和 stop_time
- 通过心跳判断上次是否正常关闭

#### 3.1.2 新增数据表: task_execution_log

```
字段说明:
- id: 主键
- instance_id: 关联 system_state 的 instance_id
- task_name: 任务名称(data_fetch/strategy_analysis/position_monitor/ai_analysis)
- task_type: 任务类型(scheduled/manual/retry)
- status: 执行状态(pending/running/success/failed/skipped)
- start_time: 开始执行时间
- end_time: 结束时间
- duration_seconds: 执行耗时
- result_summary: 执行结果摘要(JSON)
- error_message: 错误信息
- retry_count: 重试次数
- created_at: 创建时间
```

**功能说明**:
- 记录每次任务执行的完整生命周期
- 支持失败任务的重试追踪
- 便于分析任务执行效率和失败原因

### 3.2 信号队列持久化

#### 3.2.1 新增数据表: signal_queue

```
字段说明:
- id: 主键
- signal_id: 信号唯一标识(UUID)
- strategy_name: 策略名称
- symbol: 交易对
- signal_type: 信号类型(BUY/SELL)
- price: 价格
- confidence: 置信度
- signal_timestamp: 信号生成时间
- queue_status: 队列状态(pending/processing/completed/failed/expired)
- priority: 优先级(与置信度关联)
- submitted_time: 提交到队列时间
- processed_time: 处理完成时间
- order_id: 关联的订单ID
- failure_reason: 失败原因
- expiry_time: 信号过期时间(超时自动失效)
- created_at: 创建时间
```

**功能说明**:
- 所有策略信号入队前先保存到数据库
- TradeExecutor 从数据库加载未处理信号到内存队列
- 信号处理完成后更新状态为 completed
- 重启后自动恢复待处理信号

#### 3.2.2 信号生命周期管理

**信号状态流转**:
```
pending → processing → completed
                    ↓
                  failed (可重试)
                    ↓
                  expired (超时失效)
```

**过期策略**:
- 信号默认有效期: 15分钟(可配置)
- 超过有效期自动标记为 expired
- 重启时过滤掉已过期信号

### 3.3 数据获取断点续传

#### 3.3.1 新增数据表: data_fetch_progress

```
字段说明:
- id: 主键
- symbol: 交易对
- interval: K线周期
- last_fetch_time: 最后一次获取数据的时间戳
- last_complete_time: 最后一次完整数据的时间戳
- fetch_status: 获取状态(initial/fetching/completed/failed)
- total_records: 总记录数
- last_error: 最后一次错误信息
- consecutive_failures: 连续失败次数
- next_fetch_time: 计划下次获取时间
- updated_at: 更新时间
```

**功能说明**:
- 记录每个交易对的数据获取进度
- 重启后从 last_fetch_time 继续获取
- 避免重复获取已有数据
- 连续失败超过阈值时暂停该交易对的数据获取

#### 3.3.2 增量获取逻辑增强

**原有逻辑**:
```
从数据库查询最后一条记录时间戳 → 从该时间点开始增量获取
```

**增强逻辑**:
```
1. 检查 data_fetch_progress 表获取上次进度
2. 判断是否存在未完成的获取任务
3. 如果上次 fetch_status = fetching,可能中断,需重新获取
4. 更新 fetch_status = fetching
5. 执行增量获取
6. 成功后更新 fetch_status = completed 和 last_complete_time
7. 失败则记录错误并增加 consecutive_failures
```

### 3.4 订单状态同步机制

#### 3.4.1 问题分析

现有订单管理存在的问题:
- 订单提交后仅保存初始状态到数据库
- 限价单可能长时间未成交,状态未同步
- 系统重启后无法自动恢复未完成订单的监控

#### 3.4.2 订单状态同步策略

**在系统启动时执行**:
1. 查询所有状态为 NEW / PARTIALLY_FILLED 的订单
2. 调用交易所 API 同步最新状态
3. 更新数据库中的订单状态和成交数量
4. 对于已完成的买入订单,检查是否已建立持仓记录

**在运行期间定期执行**:
- 每 5 分钟扫描未完成订单
- 同步状态并更新数据库
- 超过 24 小时未成交的订单自动撤销

**新增定时任务**: `order_sync_task`
- 执行频率: 每 5 分钟
- 负责订单状态同步

### 3.5 持仓恢复机制

#### 3.5.1 启动时持仓恢复

**恢复流程**:
1. 查询数据库中 status = 'OPEN' 的所有持仓
2. 验证每个持仓的有效性:
   - 检查关联订单是否真实成交
   - 查询交易所确认持仓数量
   - 验证止损价格的合理性
3. 恢复到 PositionTracker 的监控列表
4. 立即执行一次止损检查
5. 记录恢复日志

#### 3.5.2 持仓数据一致性校验

**定期校验任务**: `position_verification_task`
- 执行频率: 每小时
- 校验内容:
  - 数据库持仓 vs 交易所实际持仓
  - 发现不一致时记录告警日志
  - 人工模式下不自动修正,仅告警
  - 自动模式下可配置是否自动平仓

### 3.6 任务幂等性保证

#### 3.6.1 数据获取任务幂等性

**策略**:
- 使用 UNIQUE 约束: (symbol, interval, open_time)
- 插入使用 INSERT OR IGNORE 语句
- 重复获取同一时间段数据不会造成重复记录

**状态**: ✅ 已实现

#### 3.6.2 策略分析任务幂等性

**问题**: 多次执行可能生成重复信号

**解决方案**:
- 在生成信号时检查是否已存在相同信号
- 信号唯一性判断: (strategy_name, symbol, signal_type, timestamp 在 5 分钟内)
- 避免短时间内生成大量重复信号

**实现位置**: `strategy_analysis_task` 函数中增加去重逻辑

#### 3.6.3 AI分析任务幂等性

**问题**: 每日分析可能重复执行

**解决方案**:
- 执行前检查 ai_analysis_log 表是否已有当天记录
- 如果已存在则跳过,除非手动指定强制重新分析
- 记录 task_execution_log 状态为 skipped

**状态**: ✅ 逻辑上可通过查询实现

### 3.7 优雅关闭流程优化

#### 3.7.1 当前关闭流程

```
收到停止信号 → 设置 shutdown_flag → 各组件依次关闭
```

#### 3.7.2 优化后的关闭流程

```
步骤 1: 收到停止信号,记录关闭原因
步骤 2: 停止接收新的交易信号
步骤 3: 等待信号队列处理完成(最多等待30秒)
步骤 4: 保存当前信号队列到数据库
步骤 5: 停止调度器(不中断正在执行的任务)
步骤 6: 停止交易执行器
步骤 7: 同步所有未完成订单状态
步骤 8: 更新所有持仓的最新数据
步骤 9: 关闭交易所连接
步骤 10: 更新 system_state 表(status=stopped, stop_time)
步骤 11: 关闭数据库连接
步骤 12: 记录关闭完成日志
```

**关键改进**:
- 分阶段关闭,优先保证数据安全
- 设置超时机制,避免无限等待
- 详细记录每个阶段的执行情况

### 3.8 系统启动恢复流程

#### 3.8.1 启动时状态检查

```
步骤 1: 生成新的 instance_id
步骤 2: 查询上次运行记录(最新的 system_state)
步骤 3: 判断上次是否正常关闭
        - 如果 status = 'stopped',正常关闭
        - 如果 status = 'running' 且心跳超过 5 分钟,判定为异常关闭
步骤 4: 如果异常关闭,执行恢复流程:
        4.1 加载未处理的信号队列
        4.2 同步所有未完成订单状态
        4.3 恢复持仓监控
        4.4 检查是否有未完成的数据获取任务
        4.5 记录恢复日志
步骤 5: 插入新的 system_state 记录
步骤 6: 启动心跳任务(每30秒更新一次)
步骤 7: 正常启动各组件
```

#### 3.8.2 恢复优先级策略

| 优先级 | 恢复内容 | 原因 |
|-------|---------|------|
| P0 | 持仓恢复与止损监控 | 防止重大资金损失 |
| P1 | 未完成订单状态同步 | 确保订单数据准确 |
| P2 | 未处理信号恢复 | 避免错失交易机会 |
| P3 | 数据获取进度恢复 | 保证数据完整性 |
| P4 | 任务调度恢复 | 恢复正常运行节奏 |

### 3.9 心跳与健康检查

#### 3.9.1 心跳任务

**新增定时任务**: `heartbeat_task`
- 执行频率: 每 30 秒
- 功能:
  - 更新 system_state.heartbeat_time
  - 检查各组件状态(调度器、交易执行器、交易所连接)
  - 如果发现组件异常,记录告警

#### 3.9.2 健康检查接口

**功能**: 提供系统健康状态查询

**检查项**:
- 数据库连接是否正常
- 交易所连接是否正常
- 调度器是否运行
- 交易执行器是否运行
- 最后一次数据更新时间
- 持仓数量统计
- 未处理信号数量

**返回结果示例**:
```
健康状态: healthy / degraded / unhealthy
数据库: OK
交易所连接: OK
调度器: Running (4 jobs)
交易执行器: Running (queue: 2)
最后数据更新: 2分钟前
持仓数量: 3
未处理信号: 2
```

### 3.10 配置变更管理

#### 3.10.1 配置快照

**机制**:
- 系统启动时将 config.yaml 的内容序列化为 JSON
- 保存到 system_state.config_snapshot
- 重启时对比配置是否变更

#### 3.10.2 热更新支持

**分类处理**:

| 配置项 | 是否支持热更新 | 更新方式 |
|-------|-------------|---------|
| 日志级别 | ✅ 支持 | 直接生效 |
| 交易对列表 | ✅ 支持 | 下次任务执行时生效 |
| 数据获取频率 | ✅ 支持 | 重新注册调度任务 |
| 风控参数 | ✅ 支持 | 下次订单检查时生效 |
| API 密钥 | ❌ 需重启 | 需重新建立连接 |
| 运行模式 | ❌ 需重启 | 涉及任务调度重构 |

**热更新命令**:
- 通过 Web UI 或命令行触发
- 重新加载配置文件
- 比对差异并应用可热更新项
- 记录配置变更日志

### 3.11 异常情况处理

#### 3.11.1 异常场景与应对策略

| 异常场景 | 检测方式 | 处理策略 |
|---------|---------|---------|
| **数据库锁** | SQLite 操作超时 | 启用 WAL 模式(已实现),增加超时重试 | 事务回滚 |
| **API 限流** | 交易所返回 429 | 指数退避重试,最多重试 3 次 | 缓存本地数据 |
| **网络断连** | 连接超时 | 自动重连,持续失败则切换离线模式 | 本地队列保存 |
| **突然断电** | 无法检测 | 依赖心跳超时判断,重启后完整恢复 | 数据库自动恢复 |
| **进程崩溃** | 心跳超时 | 重启时检测并执行完整恢复流程 | 事务日志恢复 |
| **订单部分成交** | 订单状态 PARTIALLY_FILLED | 继续监控直到完全成交或超时撤单 | 状态持久化 |
| **持仓数据不一致** | 定期校验 | 告警并记录日志,人工审核 | 双向对账 |
| **信号队列积压** | 队列长度超过阈值 | 暂停生成新信号,优先处理积压 | 过期清理 |
| **内存不足** | 系统监控 | 记录警告,建议增加配置或优化策略 | 限制缓存 |
| **磁盘空间不足** | 日志写入失败 | 自动清理过期日志和数据 | 日志轮转 |
| **交易所维护** | API 返回特定错误 | 暂停交易,仅监控持仓 | 离线模式 |
| **系统时间异常** | 心跳时间检测 | 记录告警,拒绝执行交易 | 时间校验 |

#### 3.11.2 故障恢复流程

**检测到严重错误时**:
1. 立即停止接收新任务
2. 保存当前状态到数据库
3. 记录详细错误日志
4. 尝试优雅关闭所有组件
5. 更新 system_state.status = 'crashed'
6. 发送告警通知(如果配置了通知渠道)

**重启后自动恢复**:
- 检测到上次为 crashed 状态
- 执行完整的恢复流程
- 加载所有未完成任务
- 记录恢复操作日志

#### 3.11.3 网络故障处理

**网络断连检测**:
- 主动心跳: 每30秒ping交易所API
- 被动检测: API调用超时或连接失败
- 多次重试: 连续3次失败判定为网络断连

**断网期间行为**:
```
阶段1: 检测到断网
  - 停止发送新订单
  - 保存所有待处理信号到数据库
  - 切换到离线监控模式
  - 记录断网时间和原因

阶段2: 离线模式运行
  - 持仓数据标记为"待同步"
  - 继续记录策略信号(不执行)
  - 每分钟尝试重连交易所
  - 本地队列继续接收信号

阶段3: 网络恢复
  - 检测到连接恢复
  - 立即同步所有订单状态
  - 同步持仓数据和账户余额
  - 检查止损是否触发
  - 处理积压的信号队列
  - 记录恢复日志
```

**网络恢复后数据同步优先级**:
1. **P0 - 持仓数据**: 立即同步,检查止损
2. **P1 - 订单状态**: 同步所有未完成订单
3. **P2 - 账户余额**: 更新可用资金
4. **P3 - 行情数据**: 补充缺失的K线数据
5. **P4 - 信号处理**: 处理积压信号

**长时间断网保护**:
- 断网超过30分钟: 发送告警通知
- 断网超过2小时: 记录严重告警
- 断网超过24小时: 建议人工介入检查

#### 3.11.4 断电与意外关机处理

**断电场景特点**:
- 无法执行优雅关闭流程
- 可能导致数据库文件损坏
- 内存中的数据全部丢失
- 心跳停止更新

**数据库保护机制**:

**1. SQLite WAL 模式**:
```
优势:
- 写操作不会阻塞读操作
- 崩溃后自动恢复
- 事务更安全

配置:
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
```

**2. 事务管理**:
```
原则:
- 所有关键操作必须在事务中
- 及时提交事务,避免长事务
- 失败时自动回滚

示例:
BEGIN TRANSACTION;
  -- 插入订单记录
  INSERT INTO trade_records ...
  -- 更新持仓状态
  UPDATE positions ...
COMMIT;
```

**3. 数据完整性约束**:
- 主键和外键约束
- UNIQUE 约束防止重复
- CHECK 约束验证数据合法性
- DEFAULT 值确保字段完整

**重启后数据恢复流程**:

```
步骤1: 数据库完整性检查
  - 执行 PRAGMA integrity_check
  - 如果损坏,尝试从备份恢复
  - 记录检查结果

步骤2: 心跳超时检测
  - 查询最后一次心跳时间
  - 如果超过5分钟,判定为意外关闭
  - 标记恢复模式为 "异常恢复"

步骤3: 订单状态核对
  - 查询所有状态为 NEW/PARTIALLY_FILLED 的订单
  - 逐个查询交易所实际状态
  - 更新本地数据库
  - 对于已成交但本地未记录的,补充记录

步骤4: 持仓数据验证
  - 查询数据库中 status='OPEN' 的持仓
  - 查询交易所实际持仓
  - 比对数量和均价
  - 不一致时:
    * 记录详细差异日志
    * 以交易所数据为准
    * 更新本地数据库
    * 发送告警通知

步骤5: 信号队列恢复
  - 加载 queue_status='pending' 的信号
  - 检查信号是否过期(时间戳 + 15分钟)
  - 过滤过期信号
  - 将有效信号重新加入内存队列

步骤6: 数据获取续传
  - 检查每个交易对的 last_fetch_time
  - 计算缺失的时间段
  - 标记需要补充数据的任务
  - 优先级低于持仓监控

步骤7: 系统状态记录
  - 插入新的 system_state 记录
  - 记录上次异常关闭信息
  - 记录本次恢复的详细操作
  - 更新系统启动状态
```

**断电数据丢失风险评估**:

| 数据类型 | 丢失风险 | 恢复方式 | 影响程度 |
|---------|---------|---------|----------|
| 已提交订单 | 低 | 从交易所同步 | 可恢复 |
| 持仓信息 | 低 | 从交易所同步 | 可恢复 |
| 未提交订单 | 高 | 无法恢复 | 错失交易机会 |
| 内存队列信号 | 高 | 从数据库恢复 | 部分可恢复 |
| 正在处理的任务 | 中 | 重新执行 | 可能重复执行 |
| 配置变更 | 低 | 配置文件持久化 | 可恢复 |
| 日志数据 | 中 | 部分丢失 | 影响审计 |

**断电保护最佳实践**:

1. **频繁持久化**:
   - 关键操作立即写入数据库
   - 不依赖内存缓存
   - 减小事务粒度

2. **UPS 不间断电源** (推荐):
   - 服务器使用 UPS
   - 提供5-15分钟缓冲时间
   - 足够执行优雅关闭

3. **定期备份**:
   - 每天自动备份数据库
   - 保留最近7天备份
   - 异地存储备份文件

4. **监控告警**:
   - 监控系统电源状态
   - UPS 电量低时发送告警
   - 自动执行关闭流程

#### 3.11.5 进程崩溃保护

**崩溃原因**:
- 内存溢出 (OOM)
- 未捕获的异常
- 段错误 (Segmentation Fault)
- 系统资源耗尽
- Python 解释器崩溃

**进程监控方案**:

**方案1: systemd 守护进程** (Linux推荐)
```ini
[Unit]
Description=QuantAITrade Service
After=network.target

[Service]
Type=simple
User=trader
WorkingDirectory=/path/to/QuantAITrade
ExecStart=/usr/bin/python3 main.py --mode hybrid
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**方案2: Supervisor** (跨平台)
```ini
[program:quantaitrade]
command=/usr/bin/python3 main.py --mode hybrid
directory=/path/to/QuantAITrade
autostart=true
autorestart=true
startsecs=10
startretries=3
user=trader
redirect_stderr=true
stdout_logfile=/var/log/quantaitrade.log
```

**方案3: 进程心跳监控脚本**:
```bash
#!/bin/bash
# monitor.sh - 每分钟检查进程状态

PID_FILE="/var/run/quantaitrade.pid"
LOG_FILE="/var/log/quantaitrade_monitor.log"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ! ps -p $PID > /dev/null; then
        echo "$(date): Process crashed, restarting..." >> "$LOG_FILE"
        cd /path/to/QuantAITrade
        python3 main.py --mode hybrid &
        echo $! > "$PID_FILE"
    fi
else
    echo "$(date): Starting process..." >> "$LOG_FILE"
    cd /path/to/QuantAITrade
    python3 main.py --mode hybrid &
    echo $! > "$PID_FILE"
fi
```

**崩溃后自动重启配置**:

```yaml
# config/config.yaml 新增配置
process_management:
  enable_auto_restart: true          # 是否自动重启
  max_restart_attempts: 3            # 最大重启次数
  restart_interval_seconds: 10       # 重启间隔
  crash_threshold_minutes: 5         # 崩溃判定阈值
  notify_on_crash: true              # 崩溃时发送通知
```

**崩溃保护代码实现**:

**1. 全局异常捕获**:
```python
import sys
import traceback
from loguru import logger

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    if issubclass(exc_type, KeyboardInterrupt):
        # 用户中断,正常处理
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # 记录详细的崩溃信息
    logger.critical("系统崩溃!", exc_info=(exc_type, exc_value, exc_traceback))
    
    # 保存状态到数据库
    try:
        state_manager.mark_crashed(str(exc_value))
    except:
        pass
    
    # 发送告警通知
    try:
        notifier.send_critical_alert(
            title="系统崩溃",
            message=f"{exc_type.__name__}: {exc_value}",
            traceback=traceback.format_exc()
        )
    except:
        pass

# 注册全局异常处理器
sys.excepthook = global_exception_handler
```

**2. 信号处理增强**:
```python
import signal

def handle_critical_signal(signum, frame):
    """处理关键信号"""
    signal_name = signal.Signals(signum).name
    logger.critical(f"收到关键信号: {signal_name}")
    
    # 紧急保存状态
    emergency_shutdown()
    
    # 退出
    sys.exit(1)

# 注册信号处理器
signal.signal(signal.SIGTERM, handle_critical_signal)  # 终止信号
signal.signal(signal.SIGSEGV, handle_critical_signal)  # 段错误
signal.signal(signal.SIGABRT, handle_critical_signal)  # 异常终止
```

**3. 内存监控**:
```python
import psutil
import os

def check_memory_usage():
    """检查内存使用情况"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    
    if memory_mb > 1024:  # 超过1GB
        logger.warning(f"内存使用过高: {memory_mb:.2f} MB")
        # 触发垃圾回收
        import gc
        gc.collect()
    
    if memory_mb > 2048:  # 超过2GB
        logger.critical(f"内存使用严重过高: {memory_mb:.2f} MB")
        # 发送告警
        notifier.send_alert("内存使用告警", f"当前使用: {memory_mb:.2f} MB")
    
    return memory_mb

# 定期检查(加入定时任务)
scheduler.add_job(
    func=check_memory_usage,
    trigger_type='interval',
    trigger_args={'minutes': 5},
    job_id='memory_check'
)
```

#### 3.11.6 交易所故障应对

**交易所维护检测**:
- API 返回特定错误代码
- 连续多次请求失败
- 官方公告检查(可选)

**维护期间策略**:
```
阶段1: 检测到交易所维护
  - 立即停止发送新订单
  - 切换到"只读模式"
  - 保存所有待处理信号
  - 记录维护开始时间

阶段2: 维护期间
  - 每10分钟尝试连接检查
  - 持仓数据标记为"待验证"
  - 策略继续分析但不执行
  - 维护日志持续记录

阶段3: 交易所恢复
  - 检测到API恢复正常
  - 立即执行完整的数据同步
  - 验证所有持仓和订单
  - 检查是否有紧急止损需求
  - 恢复正常交易模式
```

**紧急止损保护**:
- 维护期间无法止损的风险
- 配置"维护期间最大损失容忍度"
- 超过阈值后发送紧急告警
- 建议提前设置交易所端止损

#### 3.11.7 多重故障同时发生

**最坏情况**:
- 断电 + 断网同时发生
- UPS耗尽前网络未恢复
- 交易所同时维护

**分级保护策略**:

**一级保护 - 关键持仓**:
- 提前在交易所设置止损单
- 不依赖程序运行
- 交易所端强制止损

**二级保护 - 数据完整性**:
- 数据库 WAL 模式
- 事务原子性保证
- 定期自动备份

**三级保护 - 业务连续性**:
- 心跳机制判断异常
- 自动恢复流程
- 多重数据同步验证

**四级保护 - 人工介入**:
- 关键告警立即通知
- 提供手动恢复工具
- 详细的故障排查日志

#### 3.11.3 网络故障处理

**网络断连检测**:
- 主动心跳: 每30秒ping交易所API
- 被动检测: API调用超时或连接失败
- 多次重试: 连续3次失败判定为网络断连

**断网期间行为**:
```
阶段1: 检测到断网
  - 停止发送新订单
  - 保存所有待处理信号到数据库
  - 切换到离线监控模式
  - 记录断网时间和原因

阶段2: 离线模式运行
  - 持仓数据标记为"待同步"
  - 继续记录策略信号(不执行)
  - 每分钟尝试重连交易所
  - 本地队列继续接收信号

阶段3: 网络恢复
  - 检测到连接恢复
  - 立即同步所有订单状态
  - 同步持仓数据和账户余额
  - 检查止损是否触发
  - 处理积压的信号队列
  - 记录恢复日志
```

**网络恢复后数据同步优先级**:
1. **P0 - 持仓数据**: 立即同步,检查止损
2. **P1 - 订单状态**: 同步所有未完成订单
3. **P2 - 账户余额**: 更新可用资金
4. **P3 - 行情数据**: 补充缺失的K线数据
5. **P4 - 信号处理**: 处理积压信号

**长时间断网保护**:
- 断网超过30分钟: 发送告警通知
- 断网超过2小时: 记录严重告警
- 断网超过24小时: 建议人工介入检查

#### 3.11.4 断电与意外关机处理

**断电场景特点**:
- 无法执行优雅关闭流程
- 可能导致数据库文件损坏
- 内存中的数据全部丢失
- 心跳停止更新

**数据库保护机制**:

**1. SQLite WAL 模式**:
```
优势:
- 写操作不会阻塞读操作
- 崩溃后自动恢复
- 事务更安全

配置:
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
```

**2. 事务管理**:
```
原则:
- 所有关键操作必须在事务中
- 及时提交事务,避免长事务
- 失败时自动回滚

示例:
BEGIN TRANSACTION;
  -- 插入订单记录
  INSERT INTO trade_records ...
  -- 更新持仓状态
  UPDATE positions ...
COMMIT;
```

**3. 数据完整性约束**:
- 主键和外键约束
- UNIQUE 约束防止重复
- CHECK 约束验证数据合法性
- DEFAULT 值确保字段完整

**重启后数据恢复流程**:

```
步骤1: 数据库完整性检查
  - 执行 PRAGMA integrity_check
  - 如果损坏,尝试从备份恢复
  - 记录检查结果

步骤2: 心跳超时检测
  - 查询最后一次心跳时间
  - 如果超过5分钟,判定为意外关闭
  - 标记恢复模式为 "异常恢复"

步骤3: 订单状态核对
  - 查询所有状态为 NEW/PARTIALLY_FILLED 的订单
  - 逐个查询交易所实际状态
  - 更新本地数据库
  - 对于已成交但本地未记录的,补充记录

步骤4: 持仓数据验证
  - 查询数据库中 status='OPEN' 的持仓
  - 查询交易所实际持仓
  - 比对数量和均价
  - 不一致时:
    * 记录详细差异日志
    * 以交易所数据为准
    * 更新本地数据库
    * 发送告警通知

步骤5: 信号队列恢复
  - 加载 queue_status='pending' 的信号
  - 检查信号是否过期(时间戳 + 15分钟)
  - 过滤过期信号
  - 将有效信号重新加入内存队列

步骤6: 数据获取续传
  - 检查每个交易对的 last_fetch_time
  - 计算缺失的时间段
  - 标记需要补充数据的任务
  - 优先级低于持仓监控

步骤7: 系统状态记录
  - 插入新的 system_state 记录
  - 记录上次异常关闭信息
  - 记录本次恢复的详细操作
  - 更新系统启动状态
```

**断电数据丢失风险评估**:

| 数据类型 | 丢失风险 | 恢复方式 | 影响程度 |
|---------|---------|---------|----------|
| 已提交订单 | 低 | 从交易所同步 | 可恢复 |
| 持仓信息 | 低 | 从交易所同步 | 可恢复 |
| 未提交订单 | 高 | 无法恢复 | 错失交易机会 |
| 内存队列信号 | 高 | 从数据库恢复 | 部分可恢复 |
| 正在处理的任务 | 中 | 重新执行 | 可能重复执行 |
| 配置变更 | 低 | 配置文件持久化 | 可恢复 |
| 日志数据 | 中 | 部分丢失 | 影响审计 |

**断电保护最佳实践**:

1. **频繁持久化**:
   - 关键操作立即写入数据库
   - 不依赖内存缓存
   - 减小事务粒度

2. **UPS 不间断电源** (推荐):
   - 服务器使用 UPS
   - 提供5-15分钟缓冲时间
   - 足够执行优雅关闭

3. **定期备份**:
   - 每天自动备份数据库
   - 保留最近7天备份
   - 异地存储备份文件

4. **监控告警**:
   - 监控系统电源状态
   - UPS 电量低时发送告警
   - 自动执行关闭流程

#### 3.11.5 进程崩溃保护

**崩溃原因**:
- 内存溢出 (OOM)
- 未捕获的异常
- 段错误 (Segmentation Fault)
- 系统资源耗尽
- Python 解释器崩溃

**进程监控方案**:

**方案1: systemd 守护进程** (Linux推荐)
```ini
[Unit]
Description=QuantAITrade Service
After=network.target

[Service]
Type=simple
User=trader
WorkingDirectory=/path/to/QuantAITrade
ExecStart=/usr/bin/python3 main.py --mode hybrid
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**方案2: Supervisor** (跨平台)
```ini
[program:quantaitrade]
command=/usr/bin/python3 main.py --mode hybrid
directory=/path/to/QuantAITrade
autostart=true
autorestart=true
startsecs=10
startretries=3
user=trader
redirect_stderr=true
stdout_logfile=/var/log/quantaitrade.log
```

**方案3: 进程心跳监控脚本**:
```bash
#!/bin/bash
# monitor.sh - 每分钟检查进程状态

PID_FILE="/var/run/quantaitrade.pid"
LOG_FILE="/var/log/quantaitrade_monitor.log"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ! ps -p $PID > /dev/null; then
        echo "$(date): Process crashed, restarting..." >> "$LOG_FILE"
        cd /path/to/QuantAITrade
        python3 main.py --mode hybrid &
        echo $! > "$PID_FILE"
    fi
else
    echo "$(date): Starting process..." >> "$LOG_FILE"
    cd /path/to/QuantAITrade
    python3 main.py --mode hybrid &
    echo $! > "$PID_FILE"
fi
```

**崩溃后自动重启配置**:

```yaml
# config/config.yaml 新增配置
process_management:
  enable_auto_restart: true          # 是否自动重启
  max_restart_attempts: 3            # 最大重启次数
  restart_interval_seconds: 10       # 重启间隔
  crash_threshold_minutes: 5         # 崩溃判定阈值
  notify_on_crash: true              # 崩溃时发送通知
```

**崩溃保护代码实现**:

**1. 全局异常捕获**:
```python
import sys
import traceback
from loguru import logger

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    if issubclass(exc_type, KeyboardInterrupt):
        # 用户中断,正常处理
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # 记录详细的崩溃信息
    logger.critical("系统崩溃!", exc_info=(exc_type, exc_value, exc_traceback))
    
    # 保存状态到数据库
    try:
        state_manager.mark_crashed(str(exc_value))
    except:
        pass
    
    # 发送告警通知
    try:
        notifier.send_critical_alert(
            title="系统崩溃",
            message=f"{exc_type.__name__}: {exc_value}",
            traceback=traceback.format_exc()
        )
    except:
        pass

# 注册全局异常处理器
sys.excepthook = global_exception_handler
```

**2. 信号处理增强**:
```python
import signal

def handle_critical_signal(signum, frame):
    """处理关键信号"""
    signal_name = signal.Signals(signum).name
    logger.critical(f"收到关键信号: {signal_name}")
    
    # 紧急保存状态
    emergency_shutdown()
    
    # 退出
    sys.exit(1)

# 注册信号处理器
signal.signal(signal.SIGTERM, handle_critical_signal)  # 终止信号
signal.signal(signal.SIGSEGV, handle_critical_signal)  # 段错误
signal.signal(signal.SIGABRT, handle_critical_signal)  # 异常终止
```

**3. 内存监控**:
```python
import psutil
import os

def check_memory_usage():
    """检查内存使用情况"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    
    if memory_mb > 1024:  # 超过1GB
        logger.warning(f"内存使用过高: {memory_mb:.2f} MB")
        # 触发垃圾回收
        import gc
        gc.collect()
    
    if memory_mb > 2048:  # 超过2GB
        logger.critical(f"内存使用严重过高: {memory_mb:.2f} MB")
        # 发送告警
        notifier.send_alert("内存使用告警", f"当前使用: {memory_mb:.2f} MB")
    
    return memory_mb

# 定期检查(加入定时任务)
scheduler.add_job(
    func=check_memory_usage,
    trigger_type='interval',
    trigger_args={'minutes': 5},
    job_id='memory_check'
)
```

#### 3.11.6 交易所故障应对

**交易所维护检测**:
- API 返回特定错误代码
- 连续多次请求失败
- 官方公告检查(可选)

**维护期间策略**:
```
阶段1: 检测到交易所维护
  - 立即停止发送新订单
  - 切换到"只读模式"
  - 保存所有待处理信号
  - 记录维护开始时间

阶段2: 维护期间
  - 每10分钟尝试连接检查
  - 持仓数据标记为"待验证"
  - 策略继续分析但不执行
  - 维护日志持续记录

阶段3: 交易所恢复
  - 检测到API恢复正常
  - 立即执行完整的数据同步
  - 验证所有持仓和订单
  - 检查是否有紧急止损需求
  - 恢复正常交易模式
```

**紧急止损保护**:
- 维护期间无法止损的风险
- 配置"维护期间最大损失容忍度"
- 超过阈值后发送紧急告警
- 建议提前设置交易所端止损

#### 3.11.7 多重故障同时发生

**最坏情况**:
- 断电 + 断网同时发生
- UPS耗尽前网络未恢复
- 交易所同时维护

**分级保护策略**:

**一级保护 - 关键持仓**:
- 提前在交易所设置止损单
- 不依赖程序运行
- 交易所端强制止损

**二级保护 - 数据完整性**:
- 数据库 WAL 模式
- 事务原子性保证
- 定期自动备份

**三级保护 - 业务连续性**:
- 心跳机制判断异常
- 自动恢复流程
- 多重数据同步验证

**四级保护 - 人工介入**:
- 关键告警立即通知
- 提供手动恢复工具
- 详细的故障排查日志

## 四、具体实现模块

### 4.1 新增模块: state_manager.py

**职责**:
- 管理 system_state 表的读写
- 提供系统启动/关闭时的状态记录
- 实现心跳更新
- 判断上次运行状态

**核心方法**:
- `create_instance()`: 创建新的运行实例
- `update_heartbeat()`: 更新心跳时间
- `mark_stopped()`: 标记系统停止
- `get_last_instance()`: 获取上次运行记录
- `is_last_crashed()`: 判断上次是否异常关闭

### 4.2 新增模块: task_logger.py

**职责**:
- 管理 task_execution_log 表的读写
- 记录每次任务执行的详细日志
- 提供任务执行统计和分析

**核心方法**:
- `log_task_start()`: 记录任务开始
- `log_task_end()`: 记录任务结束
- `log_task_failed()`: 记录任务失败
- `get_task_history()`: 查询任务历史
- `get_task_statistics()`: 获取任务执行统计

### 4.3 新增模块: signal_queue_manager.py

**职责**:
- 管理 signal_queue 表的读写
- 实现信号的持久化队列
- 处理信号过期逻辑

**核心方法**:
- `enqueue_signal()`: 信号入队(保存到数据库)
- `dequeue_signals()`: 批量加载待处理信号
- `mark_signal_processing()`: 标记信号处理中
- `mark_signal_completed()`: 标记信号完成
- `mark_signal_failed()`: 标记信号失败
- `expire_old_signals()`: 清理过期信号

### 4.4 新增模块: recovery_manager.py

**职责**:
- 系统启动时的状态恢复
- 未完成任务的恢复
- 数据一致性校验

**核心方法**:
- `check_recovery_needed()`: 检查是否需要恢复
- `recover_positions()`: 恢复持仓监控
- `recover_orders()`: 同步未完成订单
- `recover_signals()`: 恢复未处理信号
- `recover_data_progress()`: 恢复数据获取进度
- `verify_data_consistency()`: 验证数据一致性

### 4.5 修改模块: main.py

**新增功能**:
- 启动时调用 RecoveryManager 执行恢复流程
- 注册心跳任务
- 注册订单同步任务
- 注册健康检查任务
- 优化关闭流程

### 4.6 修改模块: trade_executor.py

**新增功能**:
- 信号入队时同步保存到数据库
- 启动时从数据库加载未处理信号
- 信号处理完成后更新数据库状态
- 关闭时保存队列中未处理信号

### 4.7 修改模块: data/fetcher.py

**新增功能**:
- 读取和更新 data_fetch_progress 表
- 实现断点续传逻辑
- 记录获取失败次数
- 连续失败后自动暂停

### 4.8 修改模块: orchestrator/scheduler.py

**新增功能**:
- 新增 heartbeat_task
- 新增 order_sync_task
- 新增 position_verification_task
- 任务执行前后记录到 task_execution_log

## 五、数据库升级脚本

### 5.1 新增表的创建语句

所有新增表的 SQL 语句需添加到 `db_manager.init_database()` 方法中。

### 5.2 数据迁移计划

**现有系统升级步骤**:
1. 备份当前数据库文件
2. 执行新表创建语句
3. 为现有表添加缺失字段(如果需要)
4. 初始化 data_fetch_progress 表(从 kline_data 推断)
5. 验证升级成功

**向后兼容性**:
- 新增字段使用 DEFAULT 值
- 不删除现有表和字段
- 确保旧版本数据可正常读取

## 六、配置参数新增

### 6.1 config.yaml 新增配置项

```
state_management:
  enable_recovery: true                   # 是否启用恢复机制
  heartbeat_interval_seconds: 30          # 心跳间隔
  signal_expiry_minutes: 15               # 信号过期时间
  order_sync_interval_minutes: 5          # 订单同步间隔
  position_verify_interval_hours: 1       # 持仓校验间隔
  max_signal_queue_size: 50               # 信号队列最大长度
  shutdown_timeout_seconds: 30            # 关闭超时时间
  data_fetch_max_failures: 5              # 数据获取最大失败次数

task_logging:
  enable_task_log: true                   # 是否记录任务日志
  log_retention_days: 30                  # 任务日志保留天数

recovery:
  auto_recover_signals: true              # 自动恢复未处理信号
  auto_sync_orders: true                  # 自动同步订单状态
  auto_recover_positions: true            # 自动恢复持仓监控
  verify_consistency_on_start: true       # 启动时验证数据一致性
```

## 七、测试场景

### 7.1 功能测试场景

| 测试场景 | 测试步骤 | 预期结果 |
|---------|---------|---------|
| **正常停止恢复** | 启动系统 → Ctrl+C 停止 → 重新启动 | 状态正确恢复,任务继续执行 |
| **异常中断恢复** | 启动系统 → kill -9 强制终止 → 重新启动 | 检测到异常,执行完整恢复流程 |
| **信号队列恢复** | 生成信号 → 停止系统 → 重启 | 未处理信号自动恢复并执行 |
| **订单状态同步** | 提交订单 → 停止 → 重启 | 订单状态从交易所同步 |
| **持仓监控恢复** | 持有仓位 → 重启 | 持仓自动恢复监控 |
| **数据获取续传** | 获取数据中 → 中断 → 重启 | 从上次位置继续获取 |
| **重复信号过滤** | 短时间内生成相同信号 | 仅处理第一个信号 |
| **配置热更新** | 修改配置 → 触发重载 | 可热更新项立即生效 |

### 7.2 压力测试场景

| 测试场景 | 测试条件 | 验证指标 |
|---------|---------|---------|
| **大量信号积压** | 暂停处理,生成 100+ 信号 | 恢复后能正常消费队列 |
| **频繁启停** | 连续启动停止 10 次 | 状态记录正确,无数据丢失 |
| **长时间运行** | 持续运行 7 天 | 心跳正常,数据库无膨胀 |

### 7.3 异常测试场景

| 测试场景 | 模拟方式 | 预期行为 |
|---------|---------|---------|
| **数据库锁冲突** | 并发写入 | 自动重试,最终成功 |
| **API 调用失败** | Mock 返回错误 | 指数退避重试 |
| **网络中断** | 断开网络连接 | 切换离线模式,重连后恢复 |
| **突然断电** | kill -9 强制终止 | 重启后完整恢复,数据无损 |
| **进程崩溃** | raise Exception 触发崩溃 | 自动重启,执行恢复流程 |
| **长时间断网** | 断网30分钟 | 离线运行,恢复后批量同步 |
| **交易所维护** | Mock API 返回维护错误 | 只读模式,等待恢复 |
| **磁盘满** | 填满磁盘空间 | 自动清理,记录告警 |
| **内存泄漏** | 持续分配内存 | 监控告警,建议重启 |
| **时钟跳变** | 修改系统时间 | 检测告警,拒绝执行 |
| **并发订单冲突** | 同时提交多个订单 | 风控拦截,防止超仓 |
| **数据库损坏** | 强制损坏db文件 | 从备份恢复 |

## 八、日志与监控

### 8.1 关键日志点

**系统生命周期**:
- 系统启动: 记录 instance_id, 配置快照
- 恢复流程: 记录恢复的详细内容
- 心跳更新: DEBUG 级别
- 系统关闭: 记录关闭原因和耗时

**任务执行**:
- 任务开始: 记录任务名和参数
- 任务结束: 记录耗时和结果
- 任务失败: 记录错误堆栈

**信号处理**:
- 信号入队: 记录信号详情
- 信号处理: 记录处理结果
- 信号过期: 记录过期原因

### 8.2 监控指标

**系统级指标**:
- 系统运行时长
- 心跳正常率
- 恢复次数统计

**任务级指标**:
- 各任务执行频率
- 任务执行成功率
- 任务平均耗时

**业务级指标**:
- 信号队列长度
- 信号处理延迟
- 订单提交成功率
- 持仓数量变化

## 九、运维建议

### 9.1 日常运维

**定期检查**:
- 每日检查 system_state 表,确认无异常关闭
- 每周检查 task_execution_log,分析失败任务
- 每月清理过期数据(超过保留期的日志)

**数据库维护**:
- 定期执行 VACUUM 清理碎片
- 定期备份数据库文件
- 监控数据库文件大小

### 9.2 故障排查

**系统无法启动**:
1. 检查数据库文件是否损坏
2. 查看最后一次的 system_state 记录
3. 检查日志文件中的错误信息

**任务不执行**:
1. 检查调度器是否正常运行
2. 查看 task_execution_log 中的失败记录
3. 检查配置文件是否正确

**数据不一致**:
1. 执行数据一致性校验
2. 比对数据库与交易所数据
3. 手动修正或平仓处理

## 十、遗漏功能检查与完善建议

### 10.1 当前系统已实现功能评估

| 功能模块 | 完成度 | 遗漏或不完整项 |
|---------|-------|-------------|
| **基础设施** | 90% | 缺少统一的状态管理和恢复机制 |
| **数据获取** | 85% | 无断点续传,无失败重试限制 |
| **策略系统** | 70% | 仅实现 MA 交叉策略,缺少更多策略 |
| **回测引擎** | 80% | 缺少参数优化和策略对比功能 |
| **风控模块** | 90% | 功能完整,但缺少实时风险监控面板 |
| **订单执行** | 85% | 缺少订单状态同步机制 |
| **持仓跟踪** | 90% | 功能完整,需增加恢复机制 |
| **AI 分析** | 60% | 仅有基础版,建议解析结构化,无历史对比 |
| **任务调度** | 80% | 缺少任务执行日志和失败重试 |
| **Web 界面** | 40% | 仅有框架,缺少数据展示和交互 |
| **通知系统** | 30% | 模块存在但功能不完整 |
| **性能优化** | 50% | 未进行系统性优化 |

### 10.2 功能完善优先级建议

#### 优先级 P0 (本次任务必须完成)
- ✅ 系统状态持久化
- ✅ 信号队列持久化
- ✅ 数据获取断点续传
- ✅ 订单状态同步机制
- ✅ 持仓恢复机制
- ✅ 优雅关闭与恢复流程

#### 优先级 P1 (建议近期完成)
- 🔧 Web 界面数据展示(实时行情、持仓、订单)
- 🔧 AI 分析结果的结构化解析和展示
- 🔧 通知系统完善(邮件/微信/钉钉告警)
- 🔧 更多策略实现(MACD、布林带、RSI)
- 🔧 策略参数优化工具

#### 优先级 P2 (中长期规划)
- 📋 回测引擎增强(参数优化、策略对比、回测报告)
- 📋 实时风险监控面板
- 📋 多账户支持
- 📋 策略组合管理
- 📋 性能监控与优化

#### 优先级 P3 (可选增强)
- 📌 策略市场(策略分享与订阅)
- 📌 社交功能(社区讨论)
- 📌 移动端 App
- 📌 多语言支持

### 10.3 具体功能建议

#### 10.3.1 Web 界面完善

**实时数据展示**:
- 实时行情图表(K线图、技术指标)
- 持仓列表(浮动盈亏、止损价)
- 订单历史(状态、成交价、盈亏)
- 策略信号展示(信号时间、置信度)

**交互功能**:
- 手动下单界面
- 持仓管理(手动平仓、修改止损)
- 策略参数调整(实时生效)
- 系统控制(启动/停止/暂停)

**数据分析**:
- 收益曲线图
- 策略绩效对比
- 风险指标展示
- AI 分析历史查看

#### 10.3.2 AI 分析增强

**结构化建议解析**:
- 定义标准的 JSON 输出格式
- 解析 AI 建议为可执行的参数调整
- 提供建议接受/拒绝的交互界面
- 记录建议采纳历史和效果追踪

**AI 分析对比**:
- 展示历史分析记录
- 对比预测准确率
- 分析 AI 建议的有效性
- 基于反馈优化 Prompt

#### 10.3.3 通知系统完善

**通知场景**:
- 交易信号生成
- 订单成交
- 止损触发
- 风控拒绝
- 系统异常
- AI 分析完成

**通知渠道**:
- 邮件通知(已有 notifier 模块基础)
- 微信/钉钉 Webhook
- Telegram Bot
- Web 推送通知

#### 10.3.4 策略扩展

**建议新增策略**:
1. MACD 策略(趋势跟踪)
2. 布林带策略(震荡市场)
3. RSI 超买超卖策略
4. 均值回归策略
5. 网格交易策略
6. 套利策略(跨交易所)

**策略框架增强**:
- 策略热插拔机制
- 策略参数可视化调整
- 策略回测一键执行
- 策略绩效实时对比

#### 10.3.5 性能优化

**数据库优化**:
- 增加更多索引
- 分表存储历史数据
- 定期归档旧数据
- 使用连接池

**计算优化**:
- 技术指标计算缓存
- 使用 NumPy 加速计算
- 异步处理非关键任务
- 限制并发任务数量

**内存优化**:
- 限制内存中缓存的数据量
- 及时清理不再使用的对象
- 监控内存使用情况

## 十一、README 文档更新要点

### 11.1 新增章节

**系统状态管理**:
- 说明系统如何管理运行状态
- 介绍启动恢复机制
- 解释如何查看系统健康状态

**故障恢复**:
- 说明系统如何处理异常中断
- 介绍数据恢复流程
- 提供故障排查指南

**高级功能**:
- 配置热更新
- 任务执行日志查询
- 数据一致性校验

### 11.2 更新的章节

**快速开始**:
- 更新启动命令说明
- 增加恢复模式的说明

**配置说明**:
- 新增 state_management 配置项
- 新增 task_logging 配置项
- 新增 recovery 配置项

**已实现功能**:
- 更新完成度百分比
- 新增状态管理模块说明
- 新增恢复机制说明

**项目现状**:
- 更新完成度为 95%
- 列出本次完成的核心功能
- 更新待完善功能列表

### 11.3 详细说明

#### 命令行参数扩展

```bash
# 现有命令
python main.py --init-db          # 初始化数据库
python main.py --fetch-data       # 获取历史数据
python main.py --mode hybrid      # 启动混合模式

# 新增命令(建议)
python main.py --check-status     # 查看系统状态
python main.py --health-check     # 健康检查
python main.py --force-recovery   # 强制执行恢复流程
python main.py --sync-orders      # 同步订单状态
python main.py --verify-data      # 验证数据一致性
```

#### 系统状态查询

**查看最近运行记录**:
- 查询 system_state 表
- 显示启动/停止时间、运行时长
- 显示是否正常关闭

**查看任务执行历史**:
- 查询 task_execution_log 表
- 按任务名分组统计成功率
- 显示失败任务的错误信息

**查看信号队列状态**:
- 查询 signal_queue 表
- 显示待处理、处理中、已完成数量
- 显示过期信号数量

## 十二、实施计划

### 12.1 开发阶段

**阶段一: 数据库设计(1-2天)**
- 设计新增表结构
- 编写创建和升级脚本
- 测试数据库升级流程

**阶段二: 核心模块开发(3-5天)**
- 开发 state_manager.py
- 开发 task_logger.py
- 开发 signal_queue_manager.py
- 开发 recovery_manager.py

**阶段三: 集成与修改(3-4天)**
- 修改 main.py 集成恢复流程
- 修改 trade_executor.py 实现信号持久化
- 修改 data/fetcher.py 实现断点续传
- 修改 orchestrator/scheduler.py 增加新任务

**阶段四: 测试与优化(2-3天)**
- 功能测试
- 异常测试
- 压力测试
- 性能优化

**阶段五: 文档更新(1天)**
- 更新 README.md
- 编写运维文档
- 编写故障排查指南

### 12.2 总预计工作量

- 开发工作量: 10-14 天
- 测试工作量: 2-3 天
- 文档工作量: 1 天
- **总计**: 13-18 天

### 12.3 风险与应对

**技术风险**:
- SQLite 并发性能问题 → 使用 WAL 模式,限制并发写入
- 数据库文件损坏 → 定期备份,实现自动恢复

**业务风险**:
- 恢复流程错误导致重复交易 → 严格测试,增加幂等性保证
- 状态不一致导致资金损失 → 多重校验,人工审核机制

**进度风险**:
- 开发时间超出预期 → 分阶段交付,优先核心功能

## 十三、验收标准

### 13.1 功能验收

- ✅ 系统启动时能正确判断上次运行状态
- ✅ 异常关闭后重启能自动恢复所有状态
- ✅ 信号队列持久化,重启后自动恢复
- ✅ 订单状态能自动同步
- ✅ 持仓监控能自动恢复
- ✅ 数据获取支持断点续传
- ✅ 优雅关闭流程完整执行
- ✅ 任务执行日志完整记录
- ✅ 配置热更新正常工作

### 13.2 性能验收

- 系统启动时间 < 10 秒(不含数据获取)
- 恢复流程执行时间 < 30 秒
- 心跳任务无性能影响
- 数据库文件大小增长合理(< 100MB/月)

### 13.3 稳定性验收

- 连续运行 7 天无崩溃
- 频繁启停(10 次)无数据丢失
- 异常中断后恢复成功率 100%

## 十四、后续优化方向

1. **分布式部署**: 支持多实例运行,负载均衡
2. **高可用架构**: 主备切换,故障自动转移
3. **云原生改造**: 容器化部署,K8s 编排
4. **数据库升级**: 迁移到 PostgreSQL,提升并发能力
5. **微服务拆分**: 将各模块拆分为独立服务
6. **实时流处理**: 引入 Kafka/Redis Stream,提升实时性

---

## 附录A: README.md 完整更新内容

### 需要更新的章节

#### 1. 版本和完成度更新

```markdown
**当前版本**: v1.1.0
**完成度**: 95% ⭐
```

#### 2. 核心特性新增

在现有核心特性列表中增加:

```markdown
- 🔄 完整的状态管理与恢复机制
- ⏸️ 支持随时暂停、停止、重启
- 💾 关键任务状态持久化
- 🔁 断点续传与任务恢复
```

#### 3. 新增"系统状态管理"章节

```markdown
## 🔄 系统状态管理

### 核心机制

系统实现了完整的状态管理与恢复机制,确保在任何情况下(正常关闭、异常中断、崩溃)都能安全恢复:

1. **状态持久化**: 所有关键状态保存到数据库
2. **自动恢复**: 重启时自动检测并恢复上次状态
3. **数据一致性**: 确保订单、持仓等核心数据完整
4. **断点续传**: 数据获取任务支持从中断点继续

### 系统状态类型

| 状态类型 | 说明 | 恢复方式 |
|---------|------|----------|
| 系统运行状态 | 记录启动/停止时间、运行模式 | 自动记录到 system_state 表 |
| 交易信号队列 | 待处理的策略信号 | 持久化到 signal_queue 表 |
| 订单执行状态 | 未完成的订单 | 启动时自动同步状态 |
| 持仓监控 | 开仓持仓和止损价 | 自动恢复到监控列表 |
| 数据获取进度 | 每个交易对的最新数据时间 | 断点续传机制 |
| 任务执行日志 | 定时任务的执行记录 | 记录到 task_execution_log 表 |

### 启动恢复流程

系统启动时会自动执行以下恢复流程:

```
步骤1: 检测上次运行状态(正常关闭 vs 异常中断)
步骤2: 恢复持仓监控(优先级最高,防止资金损失)
步骤3: 同步未完成订单状态
步骤4: 恢复未处理的交易信号
步骤5: 恢复数据获取进度
步骤6: 启动定时任务调度
```

### 优雅关闭流程

按下 Ctrl+C 或发送停止信号时:

```
步骤1: 停止接收新信号
步骤2: 等待队列中的信号处理完成(最多30秒)
步骤3: 保存未处理信号到数据库
步骤4: 停止所有定时任务
步骤5: 同步所有订单状态
步骤6: 更新持仓数据
步骤7: 记录系统停止状态
步骤8: 关闭数据库连接
```

### 心跳与健康检查

系统运行期间每30秒更新一次心跳时间,用于判断系统是否正常运行:

- 心跳正常: 系统运行正常
- 心跳超时(>5分钟): 系统可能崩溃,下次启动执行完整恢复

### 查看系统状态

**查看最近运行记录**:
```sql
SELECT * FROM system_state ORDER BY start_time DESC LIMIT 10;
```

**查看任务执行历史**:
```sql
SELECT task_name, status, COUNT(*) as count 
FROM task_execution_log 
GROUP BY task_name, status;
```

**查看信号队列状态**:
```sql
SELECT queue_status, COUNT(*) as count 
FROM signal_queue 
GROUP BY queue_status;
```
```

#### 4. 新增"故障恢复"章节

```markdown
## 🔧 故障恢复

### 常见场景处理

#### 场景1: 正常停止后重启

```bash
# 正常关闭(Ctrl+C)
python main.py --mode hybrid

# 重启后自动恢复
python main.py --mode hybrid
```

系统会:
- ✅ 检测到上次正常关闭
- ✅ 恢复持仓监控
- ✅ 继续执行定时任务

#### 场景2: 异常中断后恢复

```bash
# 系统异常终止(kill -9 或崩溃)
# 重启时自动检测并恢复
python main.py --mode hybrid
```

系统会:
- ✅ 检测到上次异常关闭
- ✅ 执行完整恢复流程
- ✅ 同步所有订单状态
- ✅ 恢复未处理信号
- ✅ 记录恢复日志

#### 场景3: 数据获取中断

数据获取任务支持断点续传:
- 记录每个交易对的最新数据时间
- 重启后从上次位置继续获取
- 避免重复获取和数据缺失

#### 场景4: 订单部分成交

系统启动时自动同步所有未完成订单:
- 查询交易所最新状态
- 更新数据库记录
- 对于已完成的买入订单建立持仓监控

### 故障排查

#### 系统无法启动

1. 检查数据库文件: `data/quantai.db`
2. 查看日志: `logs/system.log`
3. 检查配置文件: `config/config.yaml`

#### 任务不执行

1. 检查调度器状态(日志中查找 "任务调度器")
2. 查看任务执行日志表: `task_execution_log`
3. 检查配置的任务执行时间

#### 数据不一致

1. 执行订单状态同步(系统会自动执行)
2. 检查交易所账户实际持仓
3. 查看日志中的告警信息

### 数据备份

**定期备份数据库**:
```bash
cp data/quantai.db data/backup/quantai_$(date +%Y%m%d).db
```

**恢复数据库**:
```bash
cp data/backup/quantai_20240101.db data/quantai.db
```
```

#### 5. 更新"配置说明"章节

在现有配置表格后增加:

```markdown
### 状态管理配置

| 配置分类 | 配置项 | 默认值 | 说明 |
|---------|-------|--------|------|
| **状态管理** | enable_recovery | true | 是否启用恢复机制 |
| | heartbeat_interval_seconds | 30 | 心跳间隔(秒) |
| | signal_expiry_minutes | 15 | 信号有效期(分钟) |
| | shutdown_timeout_seconds | 30 | 关闭超时时间(秒) |
| **任务日志** | enable_task_log | true | 是否记录任务日志 |
| | log_retention_days | 30 | 任务日志保留天数 |
| **恢复机制** | auto_recover_signals | true | 自动恢复未处理信号 |
| | auto_sync_orders | true | 自动同步订单状态 |
| | verify_consistency_on_start | true | 启动时验证数据一致性 |
```

#### 6. 更新"已实现的功能"章节

新增子章节:

```markdown
### ✅ 状态管理模块(100%) ⭐ **新增**
- [x] 系统状态持久化
- [x] 任务执行日志记录
- [x] 信号队列持久化
- [x] 数据获取断点续传
- [x] 订单状态自动同步
- [x] 持仓恢复机制
- [x] 优雅关闭流程
- [x] 启动时自动恢复
- [x] 心跳与健康检查
- [x] 数据一致性校验
```

#### 7. 更新"数据库表结构"说明

在项目结构章节后增加:

```markdown
### 数据库表结构

系统使用 SQLite 数据库,包含以下核心表:

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| kline_data | K线数据 | symbol, interval, open_time |
| strategy_signals | 策略信号 | strategy_name, symbol, signal_type |
| trade_records | 交易记录 | order_id, symbol, side, status |
| positions | 持仓信息 | symbol, entry_price, stop_loss_price |
| ai_analysis_log | AI分析记录 | analysis_date, suggestions |
| backtest_results | 回测结果 | strategy_name, total_return |
| **system_state** | 系统状态 | instance_id, status, heartbeat_time |
| **task_execution_log** | 任务执行日志 | task_name, status, duration_seconds |
| **signal_queue** | 信号队列 | signal_id, queue_status, priority |
| **data_fetch_progress** | 数据获取进度 | symbol, last_fetch_time, fetch_status |

**粗体**表示本次新增的状态管理相关表。
```

#### 8. 更新"开发计划"章节

修改第四阶段为:

```markdown
### 第四阶段(已完成)⭐
- ✅ Web界面框架(基础版)
- ✅ 状态管理系统设计
- ✅ 系统健壮性增强
- 🚧 状态管理系统实现(待开发)
```

#### 9. 更新"项目现状"章节

更新完成度和已实现功能:

```markdown
**当前版本**: v1.1.0
**完成度**: **95%** ⭐

### 核心成就

1. ✅ **完整的交易闭环**: 从数据获取到订单执行,全流程打通
2. ✅ **多层风控体系**: 6种止损方式,全方位保护资金安全
3. ✅ **灵活的运行模式**: 支持人工、自动、混合三种模式
4. ✅ **AI辅助决策**: 每日生成分析报告和策略建议
5. ✅ **Web可视化**: 基础界面框架,支持多页面管理
6. ✅ **状态管理系统**: 完整的设计方案,支持断点续传和故障恢复
7. ✅ **用户交互界面**: 提供策略控制、AI分析、数据展示等功能

### 技术亮点

- **数据持久化**: 所有关键状态保存到数据库
- **自动恢复**: 异常中断后自动恢复所有状态
- **优雅关闭**: 多阶段关闭流程,确保数据安全
- **心跳监控**: 实时检测系统健康状态
- **断点续传**: 数据获取支持中断恢复
- **幂等性设计**: 任务重复执行不会造成数据冲突
```

#### 10. 更新"待完善功能"列表

```markdown
### 待完善功能(优先级排序)

#### P0 级别(关键功能)
- 🔨 状态管理系统实现(已设计,待开发,预计13-18天)
- 🔨 系统集成测试(确保状态恢复机制正常)
- 📊 Web界面核心功能完善(实时行情、手动交易)

#### P1 级别(重要功能)
- 📈 完整回测中心实现
- 🤖 AI分析结果结构化解析
- ⚙️ 系统配置在线管理
- 📧 通知系统完善(邮件/微信/钉钉)
- 📈 更多策略实现(MACD、布林带、RSI)

#### P2 级别(增强功能)
- 📉 回测引擎增强(参数优化、策略对比)
- 📈 资产曲线和绩效分析
- 🎨 Web界面美化和交互增强
- 📤 数据导出功能
- ⚡ 性能优化与监控

#### P3 级别(长期规划)
- 👤 用户权限管理系统
- 🌐 多账户支持
- 🔗 多交易所支持
- 📱 移动端支持
- 🌍 国际化支持
```

#### 11. 新增"最佳实践"章节

```markdown
## 💡 最佳实践

### 首次使用建议

1. **使用测试网验证**: 首次运行务必使用币安测试网
2. **小资金起步**: 真实交易从小资金开始,逐步放大
3. **仔细回测**: 新策略必须经过充分回测验证
4. **监控日志**: 定期查看日志文件,及时发现问题
5. **定期备份**: 每周备份数据库文件

### 运维建议

**日常检查**:
- 每日查看系统运行日志
- 每周检查任务执行情况
- 每月清理过期日志和数据
- 定期检查Web界面功能是否正常

**性能优化**:
- 定期执行数据库 VACUUM
- 监控磁盘空间使用
- 合理配置任务执行频率
- 优化Web界面响应速度

**安全建议**:
- 定期更换 API 密钥
- 限制 API 权限(只需要交易权限)
- 设置合理的风控参数
- 启用 IP 白名单(交易所端)
- 保护Web界面访问安全

### 故障处理流程

1. **发现异常**: 通过日志或告警发现
2. **查看状态**: 检查 system_state 和 task_execution_log
3. **分析原因**: 查看错误日志定位问题
4. **执行恢复**: 重启系统,自动执行恢复流程
5. **验证结果**: 确认数据一致性和任务正常
6. **检查界面**: 确认Web界面显示数据正确
7. **记录总结**: 记录问题和解决方案
```

#### 12. 更新"联系方式"章节

```markdown
## 📞 支持与反馈

### 文档资源

- **项目文档**: [README.md](README.md)
- **设计文档**: [.qoder/quests/task-state-management.md](.qoder/quests/task-state-management.md)
- **状态文档**: [PROJECT_STATUS.md](PROJECT_STATUS.md)

### 常见问题

**Q: 系统异常关闭后如何恢复?**  
A: 直接重新启动即可,系统会自动检测并执行恢复流程。

**Q: 如何查看系统运行状态?**  
A: 查看 `logs/system.log` 日志文件,或查询数据库 `system_state` 表。

**Q: 信号队列积压怎么办?**  
A: 系统会自动限制队列长度,超过阈值会暂停生成新信号。

**Q: 数据获取失败如何处理?**  
A: 系统会自动重试,连续失败超过5次会暂停该交易对的数据获取。

**Q: 如何备份数据?**  
A: 定期复制 `data/quantai.db` 文件到备份目录。

**Q: Web界面无法访问怎么办?**  
A: 检查Streamlit服务是否正常运行,查看相关日志文件。

**Q: 如何在Web界面中手动交易?**  
A: 此功能正在开发中,请使用命令行或等待后续版本。

### 技术支持

如有问题或建议,请:
1. 查看项目文档和设计文档
2. 检查日志文件排查问题
3. 提交 GitHub Issue(如果开源)
```

---

### README.md 更新总结

本次更新主要增加了以下内容:

1. ✅ 新增"系统状态管理"完整章节
2. ✅ 新增"故障恢复"详细指南
3. ✅ 更新配置说明,增加状态管理配置项
4. ✅ 更新已实现功能,增加状态管理模块
5. ✅ 更新数据库表结构说明
6. ✅ 更新项目完成度(90% → 95%)
7. ✅ 更新待完善功能,按优先级分类
8. ✅ 新增"最佳实践"章节
9. ✅ 完善常见问题解答
10. ✅ 增强技术支持说明
11. ✅ 补充Web UI功能完善建议

更新后的 README.md 将更加详细和实用,帮助用户:
- 理解系统的状态管理机制
- 掌握故障恢复的方法
- 正确配置和使用系统
- 快速排查和解决问题
- 充分利用Web界面进行策略管理和监控

## 附录B: Web UI功能完善建议

### 当前Web UI功能评估

**已实现功能**:
1. ✅ 仪表盘页面 - 账户总览、持仓列表、交易记录
2. ✅ 策略控制页面 - 策略管理、信号查看、参数调整
3. ✅ AI分析页面 - 分析结果展示、建议采纳/拒绝
4. ✅ 主应用框架 - 多页面导航、系统状态指示

**待完善功能**:
1. 📈 实时行情展示 - K线图、技术指标图表
2. 📊 数据可视化增强 - 资产曲线、绩效分析
3. ⚙️ 系统管理功能 - 回测中心、配置管理
4. 📤 数据导出功能 - CSV/Excel导出
5. 👤 用户权限管理 - 登录认证、权限控制

### Web UI开发优先级建议

#### P0 - 核心功能(必须实现)
- 📈 实时K线图和指标展示
- 🛒 手动交易功能(下单、平仓)
- 📊 完整回测中心
- ⚙️ 系统配置在线管理

#### P1 - 重要功能(建议实现)
- 📈 资产曲线和绩效分析
- 🛡️ 风险监控面板
- 📤 数据导出功能
- 📋 日志查看器

#### P2 - 增强功能(可选实现)
- 🎨 主题切换和UI美化
- 👤 用户权限管理
- 📱 移动端优化
- 🌐 多语言支持

### 技术实现建议

1. **图表组件**: 使用 Plotly + Streamlit 实现专业图表
2. **实时更新**: 利用 Streamlit 缓存和自动刷新机制
3. **用户认证**: 实现简单的密码保护或OAuth集成
4. **响应式设计**: 优化移动端显示效果
5. **性能优化**: 减少数据库查询,使用缓存机制

---

**文档版本**: v1.0  
**编写日期**: 2024年  
**状态**: 待实施
