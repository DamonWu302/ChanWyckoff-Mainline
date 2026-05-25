# ChanWyckoff Mainline Agent Guide

## 项目整体介绍

ChanWyckoff Mainline（缠威主线系统）是基于缠论结构、威科夫量价关系和 A 股题材主线的中短波段量化分析工作台。

前端目标是还原 `temp/` 原生 HTML 原型的视觉、布局、间距、颜色、字体和交互状态，并沉淀为可维护、可复用、可扩展的 Next.js 组件体系。

第一阶段页面链路：

```text
系统总览 -> 今日作战台 -> 题材主线 -> 信号详情 -> 回测稳健性 -> 复盘记录
```

## 前端目录结构

```text
backend/
  app/
    api/                    FastAPI routers
    core/                   配置与环境变量
    db/                     SQLAlchemy Base、engine、session
    jobs/                   APScheduler 调度入口
  alembic/                  数据库迁移脚本
  tests/                    后端测试
app/
  globals.css              全局设计变量、基础样式和 temp 原型迁移样式
  layout.tsx               Next.js 根布局
  page.tsx                 系统总览
  today-operations/        今日作战台
  theme-mainlines/         题材主线
  signal-detail/           信号详情
  backtest/                回测稳健性
  review/                  复盘记录
  design-system/           开发环境设计系统预览
components/
  layout/                  AppShell、侧边栏、页面框架
  ui/                      Button、Panel、Metric、Status、Table、Tabs、Field 等基础组件
  pages/                   页面级组合组件
  system/                  系统级联调组件，如后端健康检查
  design-system/           设计系统预览组件
lib/
  cn.ts                    className 合并工具
  navigation.ts            导航配置
scripts/
  run_backend.sh           启动 FastAPI 开发服务
  run_frontend.sh          启动 Next.js 开发服务
```

## 后端工程规范

- 后端使用 FastAPI，入口为 `backend/app/main.py`。
- API 路由统一挂载在 `/api` 前缀下。
- 配置统一通过 `backend/app/core/config.py` 的 pydantic settings 管理。
- 数据库使用 MySQL，SQLAlchemy 负责 ORM/连接，Alembic 负责迁移。
- APScheduler 只作为调度生命周期骨架；真实数据任务在后续里程碑接入。
- 后端测试优先覆盖外部行为，例如 `/api/health` 的响应，而不是测试内部实现细节。

## 设计系统架构

设计系统从 `temp/css/app.css` 提取并迁移，核心包括：

- 颜色变量：`--bg`、`--surface`、`--fg`、`--muted`、`--accent`、`--accent-2`、`--warn`、`--danger`、`--info`。
- 字体变量：`--font-display`、`--font-body`、`--font-mono`。
- 形状变量：`--radius` 固定为 8px，组件内部按钮/输入为 7px。
- 阴影变量：`--shadow`、`--shadow-strong`。
- 动效变量：`--ease-out`、`--ease-standard`。

页面必须优先复用全局 CSS 中已经存在的布局类和组件类，例如：

- 布局：`app-shell`、`sidebar`、`main`、`topbar`、`grid`、`stack`、`split`。
- 容器：`panel`、`panel-header`、`panel-body`、`metric`、`screen-card`。
- 操作：`button`、`link-button`、`tabs`、`tab`。
- 数据展示：`status`、`table-wrap`、`ops-table`、`rule-list`、`chart`、`structure-chart`。

## 组件复用规范

- 开发页面时，必须优先复用已有组件。
- 只有在现有组件无法满足需求时，才新增组件。
- 如果已有组件可以通过 `props`、`variant`、`className` 等方式扩展，应优先扩展，而不是重新创建相似组件。
- 页面组件只负责组合和数据编排，不应重复堆叠基础样式。
- 基础 UI 组件必须保持薄封装，避免把业务规则写进 Button、Panel、Metric、Status 等通用组件。
- 业务状态标签必须复用 `Status` 组件，新增状态时优先增加 `variant` 或使用已有 `good/info/warn/danger/default` 语义。
- 卡片、表格、表单、导航、标签页、抽屉等交互，优先在 `components/ui/` 内扩展。
- 页面级状态和 mock 数据优先放在页面组件内；跨页面复用的数据结构再上移到 `lib/`。

## 后续开发注意事项

- `temp/` 是原型参考源，不要直接在生产页面中引用其中的 HTML/CSS/JS 文件。
- 设计系统预览页仅用于开发环境查看，路径为 `/design-system`。
- 新页面必须遵循“从大盘到个股”的产品信息架构，不要做成普通指标墙。
- 桌面端是第一目标，当前视觉基线保留 `min-width: 1180px` 的操作台约束。
- 不要引入装饰性大面积渐变、营销型 hero 或卡片套卡片。
- 表格需要保持紧凑、可扫描，状态标签和数字建议使用等宽字体。
- LLM 只用于解释和复盘，不应在前端文案中暗示它能直接决定交易。
- 任何与交易相关的页面必须明确展示规则证据、风险约束和失效条件。
