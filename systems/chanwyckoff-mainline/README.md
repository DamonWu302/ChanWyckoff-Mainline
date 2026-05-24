# ChanWyckoff Mainline

缠威主线系统：基于缠论结构、威科夫量价关系和 A 股题材主线的中短波段量化分析工作台。

第一阶段目标是跑通：

```text
数据入库 -> 市场环境判断 -> 题材强度 -> 趋势容量核心 -> 30 分钟三买扫描 -> 回测 -> 今日作战台展示
```

## 文档

- [产品需求文档 PRD](docs/prd.md)
- [系统设计文档](docs/system_design.md)
- [第一阶段实施任务清单](docs/phase1_tasks.md)

## 技术方向

- 后端：Python, FastAPI, SQLAlchemy, Alembic, Pandas/Polars, APScheduler
- 数据库：MySQL
- 前端：React, TypeScript, Vite
- 行情主源：TickFlow
- 题材源：东方财富/AkShare
