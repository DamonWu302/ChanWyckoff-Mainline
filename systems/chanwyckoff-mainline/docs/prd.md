# ChanWyckoff Mainline PRD

## Problem Statement

A 股中短波段交易需要同时判断大盘环境、题材主线、板块核心、个股结构、量价关系和风险约束。现在这些判断通常分散在行情软件、板块页面、自选股、人工画线、复盘笔记和回测脚本里，决策链条断裂，容易出现三个问题：

- 只看到个股 30 分钟突破，却忽略大盘是否允许进攻。
- 追到题材后排杂毛，而不是跟踪趋势容量核心。
- 信号无法复盘和回测，无法证明三买、回踩确认、威科夫量价评分是否真的提升胜率。

用户希望建立一个完整的量化分析系统，从大盘开始由面到点，识别穿越市场上涨下跌的主线，在强势题材中找到趋势容量核心，并围绕 30 分钟平台/中枢上沿突破后的工程化三买形成候选、评分、仓位、风控和复盘闭环。

第一阶段不是自动下单系统，而是决策辅助系统。它需要足够规则化、可回测、可解释，也要为后续人工确认后的半自动交易预留接口。

## Solution

构建 **ChanWyckoff Mainline（缠威主线系统）**：一个基于缠论结构、威科夫量价关系和 A 股题材主线的中短波段量化分析工作台。

系统的核心决策链路是：

```text
大盘环境 -> 题材/概念主线 -> 趋势容量核心 -> 30 分钟中枢/平台突破 -> 工程化三买 -> 仓位与风控
```

第一阶段提供：

- 大盘环境判断：基于上证指数、全 A 指数和全市场赚钱效应输出 `risk_on`、`neutral`、`risk_off`。
- 穿越主线识别：识别指数下跌时抗跌、指数转强时领涨、成交额持续放大的题材/概念。
- 趋势容量核心排序：在强势题材内寻找成交额足够、走势领先、回调抗跌、上涨带量的核心票。
- 30 分钟结构识别：用工程化中枢为主、统计平台兜底，识别平台/中枢上沿突破。
- 工程化三买状态机：输出 `proto_3buy`、`confirmed_3buy`、`failed_3buy`。
- 威科夫评分：用背景、特征、预判三段式解释量价质量，输出 `wyckoff_score`。
- 回测与稳健性报告：验证三买分层、评分分层、回踩确认、时间止损和题材增强是否有效。
- 今日作战台：把市场环境、主线、核心票、三买候选和仓位建议放在一条可操作链路上。

系统必须遵循一个边界：核心信号全规则化，LLM 只做解释、复盘和失败样本归纳，不直接决定买卖、仓位或信号有效性。

## User Stories

1. As a trader, I want to see the current market regime, so that I know whether today allows offensive trading.
2. As a trader, I want the system to classify the market as `risk_on`, `neutral`, or `risk_off`, so that my position sizing has a clear top-level gate.
3. As a trader, I want to see why the market regime was assigned, so that I can trust the conclusion instead of blindly following a label.
4. As a trader, I want the system to start from the broad market before looking at individual stocks, so that I avoid isolated pattern chasing.
5. As a trader, I want to identify themes that resist market declines, so that I can find potential through-cycle mainlines.
6. As a trader, I want to identify themes that lead when the index rebounds, so that I can focus on money-backed leadership.
7. As a trader, I want to see which themes have sustained turnover expansion, so that I avoid one-day news spikes.
8. As a trader, I want each theme to have a clear state such as resistant, emerging, confirmed, or exhausted, so that I can quickly judge its lifecycle.
9. As a trader, I want concept/theme boards to be prioritized over broad industry classifications, so that the system matches short-term A-share market language.
10. As a trader, I want industry tags to remain visible as background, so that I can still understand capacity and business context.
11. As a trader, I want each stock to have one primary theme attribution and multiple secondary tags, so that ranking and review are not muddled by multi-concept membership.
12. As a trader, I want the system to rank trend-capacity core stocks inside each theme, so that I avoid weak back-row names.
13. As a trader, I want core stock ranking to consider relative strength, capacity, leadership, resilience, and structure quality, so that one-day gains do not dominate the ranking.
14. As a trader, I want to filter out ST, suspended, delisting-risk, ChiNext, STAR Market, and Beijing Stock Exchange names, so that the universe matches my strategy scope.
15. As a trader, I want liquidity, turnover, market cap, and trend filters, so that illiquid or structurally weak names do not pollute candidates.
16. As a trader, I want the system to exclude obvious one-way downtrends, so that false rebound breakouts are reduced.
17. As a trader, I want TickFlow to provide the core market data, so that daily and 30-minute bars use one consistent source.
18. As a trader, I want 30-minute and daily bars to use forward-adjusted prices for analysis and backtesting, so that ex-right gaps do not break structures.
19. As a trader, I want real trading prices to be shown when signals are used operationally, so that analysis prices and execution prices do not get confused.
20. As a trader, I want Eastmoney/AkShare to provide first-version theme data, so that the system can run without expensive iFinD/THS dependencies.
21. As a trader, I want local Tongdaxin exports to be treated only as auxiliary snapshots, so that limited local files do not become hidden core dependencies.
22. As a trader, I want the system to store daily data snapshots, so that future theme history can accumulate from the day the system starts running.
23. As a trader, I want the system to distinguish structural backtests from theme-enhanced backtests, so that incomplete theme history does not create false confidence.
24. As a trader, I want 30-minute platforms and centers to be detected automatically, so that I can scan the full main-board universe.
25. As a trader, I want engineering Chan centers to be the primary structure definition, so that the system keeps Chan semantics while remaining testable.
26. As a trader, I want statistical platforms as a fallback, so that valid consolidation structures are not missed when strict stroke logic is ambiguous.
27. As a trader, I want each platform or center to have upper/lower bounds, duration, amplitude, overlap, and upper-edge test counts, so that I can inspect structure quality.
28. As a trader, I want the system to label first-buy, second-buy, and third-buy context, so that analysis preserves Chan vocabulary.
29. As a trader, I want the main trading strategy to focus on third-buy setups, so that the product stays aligned with the chosen breakout model.
30. As a trader, I want an excellent upper-edge breakout to become `proto_3buy`, so that I can consider a light probing position.
31. As a trader, I want a successful pullback that does not effectively re-enter the center to become `confirmed_3buy`, so that I can upgrade position size.
32. As a trader, I want failed breakouts to become `failed_3buy`, so that failure samples are retained for review.
33. As a trader, I want breakout quality to require 30-minute close confirmation, volume expansion, and candlestick quality, so that weak intrabar spikes are filtered.
34. As a trader, I want pullback confirmation to use a tolerance zone, time window, and volume contraction, so that normal retests are not misclassified as failures.
35. As a trader, I want pullback windows to be measured in 30-minute bars, so that the state machine matches the trading timeframe.
36. As a trader, I want the system to allow small pierces below the upper edge if closing behavior remains healthy, so that valid shakeouts are not filtered too harshly.
37. As a trader, I want pullback volume to be compared with breakout volume and platform average volume, so that supply re-entry is visible.
38. As a trader, I want the system to identify volume-backed failures, so that I can exit or avoid failed third-buy setups quickly.
39. As a trader, I want Wyckoff analysis to describe background, characteristics, and forecast, so that volume-price evidence is easy to read.
40. As a trader, I want Wyckoff scoring to influence signal and position grade, so that higher-quality supply-demand structures receive priority.
41. As a trader, I want Wyckoff scoring to remain rule-based in first version, so that backtests remain auditable.
42. As a trader, I want LLM summaries of signal evidence, so that dense rule outputs become easier to review.
43. As a trader, I want LLM summaries to be explicitly non-authoritative, so that they never override rule-based signals.
44. As a trader, I want `wyckoff_score >= 80` to mean a high-quality opportunity, so that candidate severity is consistent.
45. As a trader, I want 60-79 score signals to remain observable but lower priority, so that I can track them without overtrading.
46. As a trader, I want 40-59 score setups to remain in a watchlist, so that weaker structures can still be reviewed later.
47. As a trader, I want below-40 setups to be filtered from trading candidates, so that noise stays out of the active list.
48. As a trader, I want position suggestions to reflect signal stage, so that probing and confirmed positions are not treated the same.
49. As a trader, I want aggressive but bounded position rules, so that core opportunities can be sized meaningfully without removing hard risk controls.
50. As a trader, I want per-stock, per-theme, and total-position limits, so that correlated theme exposure is controlled.
51. As a trader, I want `risk_off` to suppress ordinary new positions, so that weak markets do not generate too many false breakouts.
52. As a trader, I want structure-failure stop rules, so that exits are tied to the original trade thesis.
53. As a trader, I want staged profit-taking at prior highs, measured move targets, daily resistance, and R multiples, so that gains are harvested without all-or-nothing decisions.
54. As a trader, I want time stops, so that confirmed breakouts that fail to advance do not consume capital indefinitely.
55. As a trader, I want backtests to include costs and slippage, so that results are not inflated.
56. As a trader, I want backtests to respect limit-up, limit-down, suspension, and capacity constraints, so that simulated trades are realistic.
57. As a trader, I want structural strategy backtests from 2019 onward, so that the core third-buy rules are tested across multiple market phases.
58. As a trader, I want theme-enhanced backtests only where theme history is reliable, so that the system avoids future-function bias.
59. As a trader, I want the backtest report to prove whether high-score signals outperform low-score signals, so that scoring has statistical accountability.
60. As a trader, I want the backtest report to compare `proto_3buy` and `confirmed_3buy`, so that I can quantify the value of waiting for confirmation.
61. As a trader, I want small-range parameter searches and robustness reports, so that the system avoids overfitting to one narrow parameter set.
62. As a trader, I want parameter results sliced by year and market phase, so that strategy weakness is not hidden inside aggregate results.
63. As a trader, I want signal results sliced by theme and stock contribution, so that one hot name or one sector does not dominate conclusions.
64. As a trader, I want a Today Operations page, so that I can start each trading day from one focused workspace.
65. As a trader, I want the Today Operations page to show market regime, active mainlines, core stocks, third-buy candidates, and suggested actions, so that I do not jump between unrelated tools.
66. As a trader, I want each candidate row to show signal stage, score, theme, core rank, volume evidence, and risk position, so that I can triage quickly.
67. As a trader, I want to drill from a theme into its core stocks, so that I can compare leaders and avoid back-row names.
68. As a trader, I want to drill from a stock into its 30-minute structure, so that I can inspect the platform, breakout, and pullback.
69. As a trader, I want signal details to include stop, target, timeout, and invalidation rules, so that execution planning is explicit.
70. As a trader, I want candidate filters by theme, score, stage, turnover, and market regime, so that I can narrow the list to actionable opportunities.
71. As a trader, I want an explanation panel that summarizes background, characteristics, and forecast, so that every signal has a readable thesis.
72. As a trader, I want manual confirmation states such as prepared, bought, skipped, and sold, so that research signals can become tracked trading plans.
73. As a trader, I want to record manual notes on signals, so that discretionary observations are preserved for review.
74. As a trader, I want a review page that tracks signal outcomes, so that winners and failures are not forgotten.
75. As a trader, I want failure reasons to be categorized, so that I can improve rules over time.
76. As a product designer, I want clear page priorities, so that prototype work starts with the Today Operations page and drills downward.
77. As a product designer, I want stable domain labels and states, so that UI copy, filters, tabs, and badges are consistent.
78. As a product designer, I want the decision chain to be visible in the interface, so that users understand why a stock appears.
79. As a developer, I want deep rule modules with simple interfaces, so that strategy logic can be tested independently from APIs and UI.
80. As a developer, I want data providers abstracted behind interfaces, so that TickFlow, AkShare, Tushare, or future providers can be swapped without rewriting strategy logic.
81. As a developer, I want scan results stored in MySQL, so that UI, backtests, and reviews share one persistent source of truth.
82. As a developer, I want APScheduler jobs for post-market and 30-minute scans, so that the system can run unattended once configured.
83. As a developer, I want Alembic-managed schema changes, so that database evolution is reproducible.
84. As a developer, I want API contracts for market regime, themes, core stocks, signals, backtests, and reviews, so that frontend and backend can evolve cleanly.
85. As a developer, I want tests for state machines and scoring modules, so that signal changes do not silently alter trading behavior.
86. As a reviewer, I want PRD, design, and implementation tasks to live together under the system directory, so that future contributors can understand the system quickly.

## Implementation Decisions

- The repository is organized as a quant workspace. ChanWyckoff Mainline lives under its own system directory so future systems, factors, datasets, and research notes can be added without coupling to this product.
- The product is a decision-support and research system in first phase. It does not auto-submit orders.
- The analysis flow is top-down: market regime, theme mainline, trend-capacity core stock, 30-minute structure, engineering third-buy, position and risk.
- The first trading universe is A-share main board only. ST, suspended, delisting-risk, ChiNext, STAR Market, and Beijing Stock Exchange names are excluded.
- The main timeframe is 30-minute bars. Daily bars provide environment and trend background.
- TickFlow is the main market data provider for daily bars, 30-minute bars, index data, volume, amount, and forward-adjusted prices.
- Eastmoney/AkShare is the first theme provider for concept/theme boards, board行情, constituents, turnover, and strength signals.
- Tushare and THS/iFinD are optional enhancement providers, not first-phase hard dependencies.
- Tongdaxin local exports are auxiliary snapshots only. They can support cross-sectional validation and fine-grained industry background but must not become core historical truth.
- Structure analysis and backtesting use forward-adjusted prices. Operational displays and eventual trading confirmation must map to real prices.
- Theme attribution uses concept/theme first and industry as background.
- Stocks with multiple concepts use one primary theme attribution plus secondary tags.
- Market regime is represented as `risk_on`, `neutral`, or `risk_off`.
- Through-cycle mainlines are recognized by inverse-market resilience, pro-market leadership, and sustained turnover expansion.
- Theme lifecycle labels include `resistant_theme`, `emerging_leader`, `confirmed_mainline`, and `exhausted_theme`.
- Trend-capacity core ranking uses five weighted dimensions: relative strength, capacity, leadership, resilience, and 30-minute structure quality.
- Engineering Chan center detection is the primary structure module. Statistical platform detection is the fallback module.
- The center/platform module exposes a simple input-output contract: 30-minute bars in, candidate structures with bounds and quality fields out.
- The third-buy module is a state machine over structures and subsequent bars. It emits `proto_3buy`, `confirmed_3buy`, or `failed_3buy`.
- `proto_3buy` means an excellent breakout has occurred and can support observation or probing.
- `confirmed_3buy` means the pullback did not effectively return to the center and volume-price behavior remains healthy.
- `failed_3buy` means the breakout fell back into the center, failed within the time window, or showed supply re-entry.
- Breakout confirmation requires 30-minute close above the upper edge, volume/amount expansion, and candlestick quality.
- Pullback confirmation uses a 1-8 bar window, tolerance zone, closing behavior, volume contraction, and support behavior.
- Wyckoff scoring is rule-based and organized into background, characteristics, and forecast.
- `wyckoff_score` affects signal priority and position grade. It does not independently trigger trades.
- LLM output is asynchronous explanation and review support. It cannot change rule-based signals.
- Positioning is aggressive but bounded. `proto_3buy` can suggest around 10%; `confirmed_3buy` can suggest 20%-25%; exceptional core opportunities can reach 30% single-stock cap.
- Theme exposure cap is 50%-60%. Total exposure depends on market regime.
- Exits use structure-failure stop, staged profit-taking, and time stop.
- Backtests must include transaction costs, slippage, limit-up/limit-down constraints, suspension handling, and capacity constraints.
- Backtests split into structural backtesting and theme-enhanced backtesting. Theme-enhanced conclusions are only valid where historical theme data is reliable.
- Parameter exploration uses small-range grid search and robustness reports rather than broad optimization.
- The first UI priority is Today Operations. It shows market regime, mainlines, core stocks, third-buy candidates, scores, and suggested actions.
- Secondary pages are theme mainline, stock signal detail, backtest, and review.
- The backend stack is Python, FastAPI, SQLAlchemy, Alembic, Pandas/Polars, APScheduler, and pytest.
- The database is MySQL.
- The frontend stack is React, TypeScript, and Vite.
- The core deep modules should be data providers, market regime engine, theme strength engine, core stock ranker, structure detector, third-buy state machine, Wyckoff scorer, risk engine, backtest engine, and review/LLM summarizer.

## Testing Decisions

- Tests should focus on external behavior: given market data, structures, scores, and state inputs, the module should emit the expected labels, scores, and decisions.
- Tests should avoid coupling to implementation details such as private helper ordering or intermediate variable names.
- Data provider tests should verify normalization, idempotent ingestion, provider failure handling, and source-specific field mapping.
- Market regime tests should verify `risk_on`, `neutral`, and `risk_off` outputs across representative index and breadth scenarios.
- Theme strength tests should verify relative strength, turnover expansion, breadth, and lifecycle classification.
- Core stock ranking tests should verify that high-capacity leaders outrank one-day low-capacity spikes when other evidence is weaker.
- Stock universe tests should verify exclusion of ST, suspended, delisting-risk, ChiNext, STAR Market, and Beijing Stock Exchange names.
- Structure detection tests should cover typical center/platform, converging platform, false platform, and one-way downtrend samples.
- Third-buy state machine tests should cover excellent breakout, valid pullback, allowed pierce, failed re-entry, timeout, and volume-backed failure.
- Wyckoff scoring tests should verify background, characteristics, forecast, score ranges, and score-to-signal-grade mapping.
- Risk engine tests should verify single-stock cap, theme cap, total cap, risk-off suppression, stop, target, and time-stop behavior.
- Backtest tests should verify transaction costs, slippage, next-bar execution, limit-up inability to buy, limit-down inability to sell, suspension handling, and capacity constraints.
- API tests should verify health check, market regime endpoint, theme list endpoint, core stock endpoint, signal list endpoint, signal detail endpoint, backtest summary endpoint, and review state transitions.
- Frontend tests should prioritize page-level behavior for Today Operations: rendering market regime, filtering candidates, drilling into a signal, and showing evidence fields.
- Regression fixtures should be built from small synthetic OHLCV samples first, then expanded with real historical slices once data ingestion is stable.
- The first test investment should go to deep rule modules: structure detector, third-buy state machine, Wyckoff scorer, market regime engine, and backtest engine.

## Out of Scope

- Fully automatic trading and direct order submission.
- Level2, tick-by-tick, order book, and transaction-level data.
- Machine-learning-driven signal decisions.
- LLM-driven buy/sell/position decisions.
- Strict orthodox Chan recursive implementation as the first version.
- THS/iFinD as a required first-version data dependency.
- Using current concept constituents to produce official 2019-to-present theme conclusions.
- Mobile-first trading app design.
- Multi-user permissions, team collaboration, and account management.
- Portfolio accounting that replaces a broker or PMS.
- Fundamental valuation, financial statement modeling, or long-term investment research.

## Further Notes

- The prototype should emphasize the decision chain rather than a generic dashboard. A user should be able to see why a stock is present by following market regime -> theme -> core rank -> structure -> third-buy state -> risk.
- The first page to prototype is Today Operations. It should feel like an operational trading desk, not a marketing landing page.
- The most important prototype states are `risk_on`, `neutral`, `risk_off`, `resistant_theme`, `emerging_leader`, `confirmed_mainline`, `proto_3buy`, `confirmed_3buy`, and `failed_3buy`.
- Candidate tables should be dense but readable. The user needs to compare themes and stocks repeatedly, so scanning efficiency matters more than decorative layout.
- The signal detail page should visually connect the 30-minute platform/center, breakout bar, pullback area, stop zone, target levels, and Wyckoff evidence.
- The backtest page should not only show an equity curve. It must show score stratification and whether confirmation improves results.
- The review page should preserve both rule output and discretionary human notes, because the system is a decision-support workflow before it becomes a semi-automated execution workflow.

