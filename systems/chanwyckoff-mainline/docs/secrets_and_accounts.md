# 账号、密钥与本地配置清单

本文档只记录需要人工填写的配置项，不保存真实密码、Token 或券商账号。

## MySQL

项目运行时使用独立业务账号，不使用 `root` 写入应用配置。

需要填写：

- `DATABASE_URL`：FastAPI 后端连接串。
- `MYSQL_HOST`：默认可用 `127.0.0.1`。
- `MYSQL_PORT`：默认可用 `3306`。
- `MYSQL_DATABASE`：建议 `chanwyckoff_mainline`。
- `MYSQL_APP_USER`：建议 `chanwyckoff`。
- `MYSQL_APP_PASSWORD`：后续本地创建后填写。

建议初始化 SQL：

```sql
CREATE DATABASE IF NOT EXISTS chanwyckoff_mainline
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'chanwyckoff'@'localhost'
  IDENTIFIED BY '<FILL_ME_STRONG_PASSWORD>';

GRANT ALL PRIVILEGES ON chanwyckoff_mainline.*
  TO 'chanwyckoff'@'localhost';

FLUSH PRIVILEGES;
```

## 行情主源：TickFlow

需要填写：

- `TICKFLOW_BASE_URL`：TickFlow API 地址，默认占位为 `https://api.itick.org`。
- `TICKFLOW_API_KEY`：TickFlow API Token。

第一阶段要求 TickFlow 负责：

- A 股日线前复权 K 线。
- A 股 30 分钟前复权 K 线。
- 指数行情。
- 成交量、成交额等基础量价字段。

## 题材第一源：东方财富 / AkShare

需要填写：

- `EASTMONEY_BASE_URL`：东方财富来源地址，默认占位为 `https://quote.eastmoney.com`。

AkShare 本身通常不需要账号密钥，但部署环境要能访问对应数据源。若后续某些接口不稳定，再增加备用源配置。

## 本地通达信快照

需要填写：

- `TDX_SNAPSHOT_DIR`：本地通达信导出快照目录。

约束：

- 通达信快照只作为成交额、市值、换手等补充数据。
- 核心扫描流程不能依赖通达信快照一定存在。

## LLM 复盘辅助

需要填写：

- `LLM_PROVIDER`：如 `deepseek`、`openai` 或后续自建网关。
- `LLM_API_KEY`：对应 Provider 的 API Key。

约束：

- LLM 只做解释、复盘摘要、失败样本归纳。
- 核心信号、仓位、风控必须由规则引擎输出，不能由 LLM 直接决定。

## 后续交易确认预留

第一阶段不接自动下单。后续半自动确认可能需要：

- 券商客户端路径。
- 人工确认账号标识。
- 通知渠道 Token。
- 邮件或企业微信 Webhook。

这些配置在真实接入前只保留文档占位。
