# Ledgerline 功能测试指南

## 目录

1. [测试环境准备](#测试环境准备)
2. [交易模块测试](#交易模块测试)
3. [市场数据模块测试](#市场数据模块测试)
4. [技术指标模块测试](#技术指标模块测试)
5. [策略系统测试](#策略系统测试)
6. [AI 聊天模块测试](#ai-聊天模块测试)
7. [回测系统测试](#回测系统测试)
8. [监控告警模块测试](#监控告警模块测试)
9. [前端页面测试](#前端页面测试)
10. [Bug 记录](#bug-记录)

---

## 测试环境准备

### 1. 启动后端服务

```bash
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

验证服务启动成功：
- 访问 http://localhost:8000/health 应返回 `{"status": "ok", "service": "ledgerline-api"}`
- 访问 http://localhost:8000/docs 应看到 API 文档

### 2. 启动前端服务

```bash
cd apps/web
npm run dev
```

验证服务启动成功：
- 访问 http://localhost:3000 应看到首页

### 3. 测试工具

- **前端测试**：直接在浏览器中操作
- **API 测试**：使用浏览器开发者工具或 curl 命令
- **API 密钥**：默认 `dev-key`（开发环境）

---

## 交易模块测试

### 1. 工作区管理

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 1.1 | 创建工作区 | POST `/api/v1/trading/workspaces`<br>Body: `{"name": "测试工作区"}` | 返回工作区对象，包含 id 和 name |
| 1.2 | 查询工作区 | GET `/api/v1/trading/workspaces/{id}` | 返回工作区详情 |

### 2. 投资组合管理

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 2.1 | 创建投资组合 | POST `/api/v1/trading/portfolios`<br>Body: `{"workspace_id": 1, "name": "测试组合"}` | 返回投资组合对象 |
| 2.2 | 查询投资组合 | GET `/api/v1/trading/portfolios/{id}` | 返回投资组合详情 |
| 2.3 | 获取组合摘要 | GET `/api/v1/trading/portfolios/{id}/summary` | 返回组合持仓汇总 |

### 3. 交易记录

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 3.1 | 记录开仓交易 | POST `/api/v1/trading/transactions`<br>Body: `{"portfolio_id": 1, "market": "crypto", "symbol": "BTCUSDT", "side": "long", "type": "open", "price": 100000, "quantity": 0.1, "executed_at": "2024-01-01T00:00:00"}` | 返回交易记录，自动创建持仓 |
| 3.2 | 记录加仓交易 | POST `/api/v1/trading/transactions`<br>Body: `{"portfolio_id": 1, "market": "crypto", "symbol": "BTCUSDT", "side": "long", "type": "add", "price": 105000, "quantity": 0.1, "executed_at": "2024-01-02T00:00:00"}` | 返回交易记录，持仓数量增加 |
| 3.3 | 查询交易列表 | GET `/api/v1/trading/transactions` | 返回交易列表 |
| 3.4 | 查询指定组合交易 | GET `/api/v1/trading/transactions?portfolio_id=1` | 返回指定组合的交易列表 |

### 4. 持仓管理

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 4.1 | 查询持仓详情 | GET `/api/v1/trading/positions/{id}` | 返回持仓详情，包含平均成本和数量 |
| 4.2 | 查询组合持仓 | GET `/api/v1/trading/positions?portfolio_id=1` | 返回组合的所有持仓 |
| 4.3 | 平仓 | POST `/api/v1/trading/positions/{id}/close` | 持仓状态变为 closed |

### 5. 自选列表

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 5.1 | 添加自选 | POST `/api/v1/trading/watchlist`<br>Body: `{"portfolio_id": 1, "market": "crypto", "symbol": "BTCUSDT"}` | 返回自选项目 |
| 5.2 | 查询自选 | GET `/api/v1/trading/portfolios/{id}/watchlist` | 返回自选列表 |
| 5.3 | 更新自选 | PUT `/api/v1/trading/watchlist/{id}`<br>Body: `{"alert_price_high": 110000, "alert_price_low": 90000}` | 更新成功 |
| 5.4 | 删除自选 | DELETE `/api/v1/trading/watchlist/{id}` | 返回 `{"status": "deleted"}` |

---

## 市场数据模块测试

### 1. OHLCV 数据

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 1.1 | 获取 K 线数据 | GET `/api/v1/market/ohlcv?market=crypto&symbol=BTCUSDT&interval=1d&limit=10` | 返回 OHLCV 数据列表 |
| 1.2 | 获取多个间隔 | GET `/api/v1/market/ohlcv?market=crypto&symbol=BTCUSDT&interval=1h&limit=24` | 返回 24 小时 K 线数据 |

### 2. 实时价格

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 2.1 | 获取当前价格 | GET `/api/v1/market/price/current?market=crypto&symbol=BTCUSDT` | 返回当前价格 |
| 2.2 | 获取多个价格 | GET `/api/v1/market/price/batch?market=crypto&symbols=BTCUSDT,ETHUSDT` | 返回多个币种价格 |

### 3. 市场状态

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 3.1 | 获取市场列表 | GET `/api/v1/market/exchanges` | 返回支持的交易所列表 |
| 3.2 | 获取交易对 | GET `/api/v1/market/symbols?market=crypto` | 返回交易对列表 |

---

## 技术指标模块测试

### 1. 移动平均线

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 1.1 | 计算 SMA | GET `/api/v1/indicators/sma?market=crypto&symbol=BTCUSDT&interval=1d&period=20` | 返回 SMA 指标数据 |
| 1.2 | 计算 EMA | GET `/api/v1/indicators/ema?market=crypto&symbol=BTCUSDT&interval=1d&period=20` | 返回 EMA 指标数据 |

### 2. MACD

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 2.1 | 计算 MACD | GET `/api/v1/indicators/macd?market=crypto&symbol=BTCUSDT&interval=1d` | 返回 MACD、信号线、柱状图数据 |

### 3. RSI

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 3.1 | 计算 RSI | GET `/api/v1/indicators/rsi?market=crypto&symbol=BTCUSDT&interval=1d&period=14` | 返回 RSI 值，范围 0-100 |

### 4. 布林带

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 4.1 | 计算布林带 | GET `/api/v1/indicators/bollinger?market=crypto&symbol=BTCUSDT&interval=1d&period=20` | 返回上轨、中轨、下轨数据 |

### 5. 其他指标

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 5.1 | 计算动量 | GET `/api/v1/indicators/momentum?market=crypto&symbol=BTCUSDT&interval=1d&period=14` | 返回动量值 |
| 5.2 | 计算 ROC | GET `/api/v1/indicators/roc?market=crypto&symbol=BTCUSDT&interval=1d&period=14` | 返回 ROC 值 |
| 5.3 | 计算成交量均线 | GET `/api/v1/indicators/volume_ma?market=crypto&symbol=BTCUSDT&interval=1d&period=20` | 返回成交量均线数据 |

---

## 策略系统测试

### 1. 策略列表

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 1.1 | 获取策略列表 | GET `/api/v1/strategies/list` | 返回所有可用策略 |

### 2. 策略信号

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 2.1 | RSI 策略信号 | GET `/api/v1/strategies/rsi?market=crypto&symbol=BTCUSDT&interval=1d` | 返回 RSI 策略信号（buy/sell/hold） |
| 2.2 | MACD 策略信号 | GET `/api/v1/strategies/macd?market=crypto&symbol=BTCUSDT&interval=1d` | 返回 MACD 策略信号 |
| 2.3 | 均线交叉策略 | GET `/api/v1/strategies/moving_average_cross?market=crypto&symbol=BTCUSDT&interval=1d` | 返回均线交叉信号 |
| 2.4 | 布林带策略 | GET `/api/v1/strategies/bollinger?market=crypto&symbol=BTCUSDT&interval=1d` | 返回布林带信号 |

### 3. 多策略共识

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 3.1 | 获取策略共识 | GET `/api/v1/strategies/consensus?market=crypto&symbol=BTCUSDT&interval=1d` | 返回综合信号和各策略投票结果 |

---

## AI 聊天模块测试

### 1. AI 状态

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 1.1 | 检查 AI 状态 | GET `/api/v1/ai/status` | 返回 AI 模块状态和可用模型 |

### 2. AI 聊天

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 2.1 | 基础聊天 | POST `/api/v1/ai/chat`<br>Body: `{"message": "你好"}` | 返回 AI 回复 |
| 2.2 | 市场分析 | POST `/api/v1/ai/chat`<br>Body: `{"message": "分析一下 BTC 的走势", "include_context": true}` | 返回带市场上下文的分析 |
| 2.3 | 组合分析 | POST `/api/v1/ai/chat/portfolio` | 返回投资组合分析 |
| 2.4 | 信号分析 | POST `/api/v1/ai/chat/signal?strategy=rsi&symbol=BTCUSDT&market=crypto&interval=1d` | 返回策略信号分析 |

### 3. AI 上下文

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 3.1 | 获取上下文 | GET `/api/v1/ai/context` | 返回当前 AI 使用的交易和市场上下文 |

---

## 回测系统测试

### 1. 运行回测

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 1.1 | 单策略回测 | POST `/api/v1/backtesting/run`<br>Body: `{"strategy": "rsi", "market": "crypto", "symbol": "BTCUSDT", "interval": "1d", "start_date": "2024-01-01", "end_date": "2024-06-30", "initial_capital": 10000}` | 返回回测结果和性能指标 |
| 1.2 | 多策略回测 | POST `/api/v1/backtesting/run`<br>Body: `{"strategy": "consensus", "market": "crypto", "symbol": "BTCUSDT", "interval": "1d", "start_date": "2024-01-01", "end_date": "2024-06-30", "initial_capital": 10000}` | 返回多策略共识回测结果 |

### 2. 回测指标验证

验证返回的性能指标包含：
- 总收益率 (total_return)
- 年化收益率 (annualized_return)
- 最大回撤 (max_drawdown)
- 夏普比率 (sharpe_ratio)
- 胜率 (win_rate)
- 交易次数 (total_trades)

---

## 监控告警模块测试

### 1. 告警规则管理

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 1.1 | 创建价格高于告警 | POST `/api/v1/monitoring/alerts/price`<br>Body: `{"name": "BTC 价格高于告警", "market": "crypto", "symbol": "BTCUSDT", "type": "price_above", "threshold": 110000, "severity": "warning"}` | 返回告警规则 |
| 1.2 | 创建价格低于告警 | POST `/api/v1/monitoring/alerts/price`<br>Body: `{"name": "BTC 价格低于告警", "market": "crypto", "symbol": "BTCUSDT", "type": "price_below", "threshold": 90000, "severity": "critical"}` | 返回告警规则 |
| 1.3 | 创建价格变动告警 | POST `/api/v1/monitoring/alerts/price`<br>Body: `{"name": "BTC 价格变动告警", "market": "crypto", "symbol": "BTCUSDT", "type": "price_change", "threshold": 5, "severity": "info"}` | 返回告警规则 |
| 1.4 | 查询告警规则 | GET `/api/v1/monitoring/alerts/rules` | 返回所有告警规则 |
| 1.5 | 启用/禁用规则 | PATCH `/api/v1/monitoring/alerts/rules/{id}/toggle` | 返回 `{"success": true}` |
| 1.6 | 删除规则 | DELETE `/api/v1/monitoring/alerts/rules/{id}` | 返回 `{"success": true}` |

### 2. 价格监控

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 2.1 | 启动价格监控 | POST `/api/v1/monitoring/monitor/start?market=crypto&symbol=BTCUSDT&interval=5` | 返回成功消息 |
| 2.2 | 获取监控列表 | GET `/api/v1/monitoring/monitor/symbols` | 返回正在监控的交易对 |
| 2.3 | 停止价格监控 | POST `/api/v1/monitoring/monitor/stop?market=crypto&symbol=BTCUSDT` | 返回成功消息 |

### 3. 告警通知

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 3.1 | 查询告警通知 | GET `/api/v1/monitoring/alerts/notifications` | 返回告警通知列表 |
| 3.2 | 标记已读 | PATCH `/api/v1/monitoring/alerts/notifications/{id}/read` | 返回成功消息 |
| 3.3 | 全部标记已读 | PATCH `/api/v1/monitoring/alerts/notifications/read-all` | 返回标记数量 |

### 4. WebSocket 实时推送

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 4.1 | 连接 WebSocket | 连接 `ws://localhost:8000/api/v1/monitoring/ws` | 连接成功 |
| 4.2 | 接收价格更新 | 启动价格监控后观察 | 收到 `{"type": "price", "data": {...}}` |
| 4.3 | 接收告警推送 | 触发告警规则后观察 | 收到 `{"type": "alert", "data": {...}}` |

---

## 前端页面测试

### 1. 首页

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 1.1 | 访问首页 | 打开 http://localhost:3000 | 显示首页内容 |

### 2. Dashboard 页面

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 2.1 | 访问 Dashboard | 点击左侧导航 "Dashboard" | 显示组合概览和最近交易 |
| 2.2 | 检查数据加载 | 观察页面数据 | 组合摘要和交易列表正常显示 |

### 3. AI 聊天页面

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 3.1 | 访问聊天页面 | 点击左侧导航 "AI Chat" | 显示聊天界面 |
| 3.2 | 发送消息 | 输入消息并发送 | AI 回复显示在聊天框中 |

### 4. 投资组合页面

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 4.1 | 访问组合页面 | 点击左侧导航 "Portfolio" | 显示投资组合列表 |
| 4.2 | 查看持仓 | 点击某个组合 | 显示持仓详情 |

### 5. 交易页面

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 5.1 | 访问交易页面 | 点击左侧导航 "Trade" | 显示交易表单 |
| 5.2 | 提交交易 | 填写交易信息并提交 | 交易成功，页面刷新 |

### 6. 通知页面

| 测试步骤 | 操作 | 预期结果 | 状态 |
|---------|------|---------|------|
| 6.1 | 访问通知页面 | 点击左侧导航 "Notifications" | 显示通知列表 |

---

## Bug 记录

| 序号 | 模块 | 问题描述 | 复现步骤 | 预期结果 | 实际结果 | 严重程度 | 状态 |
|-----|------|---------|---------|---------|---------|---------|------|
| 1 | | | | | | | |
| 2 | | | | | | | |
| 3 | | | | | | | |
| 4 | | | | | | | |
| 5 | | | | | | | |
| 6 | | | | | | | |
| 7 | | | | | | | |
| 8 | | | | | | | |
| 9 | | | | | | | |
| 10 | | | | | | | |

### 严重程度说明

- **Critical**：核心功能无法使用，系统崩溃
- **High**：重要功能异常，影响主要业务流程
- **Medium**：次要功能异常，不影响核心流程
- **Low**：界面问题、小缺陷、建议改进

### 状态说明

- **Open**：已发现，待修复
- **In Progress**：修复中
- **Fixed**：已修复，待验证
- **Closed**：已验证通过