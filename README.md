# Stock Quant Workspace

量化研究与交易辅助工作区。当前第一套系统是 **ChanWyckoff Mainline**，中文名 **缠威主线系统**。

这个仓库按系统/策略分目录组织，方便后续继续加入其他量化因子、策略原型和交易工作台。

## Systems

- [ChanWyckoff Mainline](systems/chanwyckoff-mainline)：基于缠论结构、威科夫量价关系和 A 股题材主线的中短波段量化分析工作台。

## Repository Layout

```text
systems/
  chanwyckoff-mainline/
    docs/
      system_design.md
      phase1_tasks.md
```

后续新增内容建议按意图放置：

- `systems/`：完整策略系统或交易工作台。
- `factors/`：可复用量化因子。
- `datasets/`：数据字典、样例数据和离线数据说明。
- `research/`：一次性研究、实验和验证记录。
