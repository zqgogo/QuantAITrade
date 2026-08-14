# Reports 统计功能整改文档

更新时间：2026-08-14

## 背景

Reports 统计功能（`get_report_stats` + `GET /api/v1/trading/reports/stats` + 前端 Reports 页面）于 2026-08-07 开发完成，但**从未提交**，当前处于未提交工作区。该功能前后端契约已对齐且类型检查通过，但存在若干质量缺陷，需补齐后再提交。

## 现状（整改前）

- 后端 `period` 参数无校验，非法值被静默当作 `all`。
- `realized_pnl` 未扣除手续费（`pnl = sell_revenue - buy_cost`）。
- `router.py` / `service.py` 行尾无换行。
- 无任何 Reports 相关测试。
- 前端请求失败仅 `console.error`，无错误提示。

## 任务清单

| # | 任务 | 状态 | 验收标准 |
|---|------|------|---------|
| 1 | 后端 `period` 参数校验（`Literal`） | ✅ | 非法 period 返回 422 |
| 2 | `realized_pnl` 扣除持仓手续费 | ✅ | 手续费计入净盈亏 |
| 3 | 行尾换行修复 | ✅ | ruff / git diff 无缺换行 |
| 4 | 测试库隔离 + Reports 测试 | ✅ | `pytest -q` 全绿，不读写真实库 |
| 5 | 前端错误/空态处理 | ✅ | 请求失败有可见提示 |
| 6 | 全量回归验证 | ✅ | pytest + ruff + tsc 通过 |
| 7 | 提交 | ✅ | git status 干净 |

## 口径说明

- 已实现盈亏（realized_pnl）按**平仓日**归属到某一天，与交易跨期无关。
- `realized_pnl = 卖出收入 - 买入成本 - 该持仓全部手续费`。
- `total_fee` 按交易执行时间统计区间内全部手续费。
- 非法 `period` 由后端返回 422，前端仅允许 `week | month | all`。
- `week` 从本周一 00:00 起，`month` 从本月 1 日 00:00 起，`all` 不限。

## 验收步骤

```bash
# 后端测试（隔离临时库）
cd apps/api && source .venv/bin/activate && pytest -q

# 代码检查
ruff check app tests

# 前端类型检查
cd apps/web && npx tsc --noEmit

# 手工验证非法 period 返回 422
curl -H "X-API-Key: dev-secret-key" \
  "http://localhost:8000/api/v1/trading/reports/stats?period=year"
```

## 已完成记录

- 2026-08-14：`period` 用 `Literal["week","month","all"]` 约束，非法值返回 422；`get_report_stats` 对未知 period 抛 `ValueError`。
- 2026-08-14：`realized_pnl` 扣除持仓全部手续费。
- 2026-08-14：新增 `tests/conftest.py` 用临时 SQLite 隔离测试，不再污染 `var/trading.db`；修复 `test_ai_config` 依赖本地 `llm.config.json` 的问题，强制加载 demo 配置。
- 2026-08-14：新增 `tests/test_reports_api.py` 6 个用例（空数据、开平仓净盈亏、部分减仓、未平仓排除、非法 period、响应结构）。
- 2026-08-14：前端 Reports 页面增加错误提示与请求取消保护。
- 2026-08-14：前端构建产物 `next-env.d.ts` / `tsconfig.tsbuildinfo` 停止跟踪，加入 `.gitignore`。

## 后续 P0（独立于本项）

- 2026-08-14 ✅ 清理后端全部 Ruff 未使用导入/f-string（ai、backtesting、market、monitoring、strategies、trading/schemas），`ruff check app tests` 全绿；顺手修复 `chat_signal` 端点 signal prompt 被丢弃的真实 bug。
- 2026-08-14 ✅ 补齐前端 ESLint flat config（`eslint.config.mjs`），修复 lint 全部 errors/warnings，`npm run lint` 全绿。
- 2026-08-14 ✅ 建立 GitHub Actions CI（`.github/workflows/ci.yml`）：后端 pytest + ruff，前端 lint + tsc + build。
