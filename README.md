# QuantAITrade

QuantAITrade 是一个面向加密货币的智能量化交易系统，核心目标是把行情数据、策略信号、风控、交易执行、AI 分析和 Web/API 管理界面串成一个可运行的闭环。

> 本项目仅供学习、研究和策略验证使用，不构成投资建议。实盘交易前必须先使用测试网和小资金充分验证。

## 当前状态

当前代码已经具备主流程骨架和多数核心模块，适合继续做功能完善、稳定性验证和实盘前加固。

- 数据链路：Binance/ccxt 行情获取、SQLite 存储、历史回补和增量更新。
- 策略系统：策略基类、MA 交叉策略、参数校验、信号生成。
- 回测引擎：基础回测流程、权益曲线、绩效指标计算。
- 风控执行：订单风控、止损计算、订单管理、持仓跟踪、交易执行器。
- 调度运行：manual、auto、hybrid 三种运行模式，基于 APScheduler 执行定时任务。
- AI 分析：数据准备、Prompt 构建、OpenAI 调用、建议解析和分析结果存储。
- Web 管理：Streamlit 仪表盘、策略控制、AI 分析、系统设置等页面框架。
- REST API：FastAPI 服务、JWT 认证、策略/订单/持仓/AI/系统状态等基础接口。
- 状态管理：系统状态、任务日志、信号队列、恢复管理、健康检查等工具模块。

更细的进度和下一步见 [PROJECT_STATUS.md](PROJECT_STATUS.md)。

## 目录结构

```text
QuantAITrade/
├── main.py                  # 主系统入口
├── quickstart.sh            # 本地快速启动辅助脚本
├── requirements.txt         # Python 依赖
├── README.md                # 最新项目文档
├── PROJECT_STATUS.md        # 最新进度与下一步
├── config/                  # YAML 配置与配置加载器
├── data/                    # 数据模型、数据库、行情获取
├── src/
│   ├── ai/                  # AI 分析
│   ├── api/                 # FastAPI 接口
│   ├── backtest/            # 回测引擎
│   ├── execution/           # 风控、订单、持仓、执行
│   ├── orchestrator/        # 调度器
│   ├── strategy/            # 策略系统
│   ├── ui/                  # Streamlit Web UI
│   └── utils/               # 状态、恢复、通知、性能等工具
├── test_system.py           # 基础系统功能测试
└── test_task_state_management.py
```

## 环境准备

要求：

- Python 3.10+
- 稳定网络连接
- Binance API Key，实盘/测试网交易功能需要
- OpenAI API Key，AI 分析功能需要

安装依赖：

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

也可以使用快速脚本：

```bash
./quickstart.sh
```

## 配置

复制环境变量模板：

```bash
cp .env.example .env
```

然后编辑 `.env`，至少关注：

```bash
BINANCE_API_KEY=...
BINANCE_API_SECRET=...
BINANCE_TESTNET=true
OPENAI_API_KEY=...
API_SECRET_KEY=...
API_PASSWORD=...
```

主要业务配置在：

- `config/config.yaml`：运行模式、交易对、风控、数据、UI、调度、恢复等主配置。
- `config/strategy_params.yaml`：策略参数。
- `config/ai_settings.yaml`：AI 分析设置。

## 常用命令

初始化数据库：

```bash
python main.py --init-db
```

获取历史行情：

```bash
python main.py --fetch-data
```

启动主系统：

```bash
python main.py --mode manual
python main.py --mode auto
python main.py --mode hybrid
```

启动 Web UI：

```bash
streamlit run src/ui/app.py
```

默认访问：

```text
http://localhost:8501
```

启动 API 服务：

```bash
python -m src.api.server
```

默认 API 文档：

```text
http://localhost:8000/docs
```

运行基础测试：

```bash
python test_system.py
python test_task_state_management.py
```

## 运行模式

- `manual`：系统生成信号，不自动交易，适合策略验证。
- `auto`：信号通过风控后自动执行，并持续监控持仓。
- `hybrid`：自动执行策略交易，AI 建议保留人工审核空间，当前推荐模式。

## 安全提示

- 默认优先使用 `BINANCE_TESTNET=true`。
- `.env` 不应提交到 Git。
- 当前还有若干风控、UI、AI 效果追踪和集成测试待完善，实盘前必须补齐并压测。
- 加密货币波动剧烈，任何自动化交易都需要独立风控、日志监控和人工兜底。
