# HarnessOS 项目规则

本仓库是个人 AI 工作台的轻量受管资产中枢，管理资产索引、恢复配方以及 Rules 与 Skills 的既有发布链。

## 源与边界

- `global/AGENTS.md` 是跨项目 Rule 正文的事实源；`skills/` 是自有 Skill 的事实源；`vendor/` 是第三方 Skill 的原样副本；`workflows/` 是 Workflow 正文的事实源；`inventory/` 管理资产分类、结构化资产记录与工作台配置档。
- `catalog.html` 与 `CATALOG.md` 是从同一事实源生成的快速浏览页和精简文本索引，均不手工修改；不能直接修改各 Agent 的 Rules 或 Skills 发布目标。
- `vendor/` 不手工修补；上游更新时整目录替换，并在 `vendor/SOURCES.md` 登记来源、许可证和迁移条件。第三方 Skill 的完整运行依赖必须随目录保留。
- 仓库只保存索引和恢复配方，不保存安装包、完整配置、账号、许可证正文、密钥、token、私钥、私有分享链接、生产配置或机器绝对路径。备份位置使用不含凭据的逻辑引用。
- 只有用户明确要求登记、纳管或更新某项资产时，才能探索并写入对应记录；不得主动扫描已安装软件、枚举整机环境、从普通对话推断个人偏好或设置后台巡检。
- 软件安装形态、版本通道、主要用途和恢复范围等偏好由用户确认；动态事实在真实迁移前重新核验官方来源、兼容性、支持版本与许可条件。
- 每项受管资产区分用户自产与第三方，并声明是否跟踪外部上游更新；用户自产资产没有上游更新，目录显示“不适用”，其仓库内修订仍正常版本化。
- 跟踪上游更新的资产用 `[upstream]` 登记查询渠道、定位符与最近核验版本；找不到可核验渠道的资产标为 `unavailable` 并说明原因，渠道切换先登记 `pending_*` 与生效条件、核验一致后于下次版本更新生效。
- 新资产类型先登记到 `inventory/taxonomy.toml`，再按 `inventory/README.md` 的统一词条模板创建事实源；结构化资产不再按类型另设字段集，不适用字段留空；未来类型仍复用统一资产 ID、关系、生命周期、目录和配置档，不另建平行管理体系。

## 目录与发布

| 用途 | 命令 |
|---|---|
| 校验资产源、引用与两种目录产物 | `python scripts/catalog.py check` |
| 从事实源重建 HTML 与 Markdown 目录 | `python scripts/catalog.py render` |
| 查询受管资产 | `python scripts/catalog.py list` |
| 生成配置档恢复清单 | `python scripts/catalog.py plan <profile> [--satisfied <asset-id>]` |
| 批量核验上游渠道最新稳定版本（只读） | `python scripts/versions.py` |
| 重建目录并发布 Rules 与 Skills | `python scripts/sync.py` |
| 只检查目录与发布漂移 | `python scripts/sync.py --check` |
| 单独发布全局 Rules | `python scripts/publish_global.py` |
| 单独发布全部 Skills | `python scripts/publish_skills.py` |

- `catalog.py plan` 只生成恢复清单，不安装软件、连接服务或恢复数据。
- `sync.py` 普通模式先重建 `catalog.html` 与 `CATALOG.md`，再沿用既有路径发布 Rules 与 Skills；`--check` 只检查，不修改文件或发布目标。Inventory 与 Workflows 不发布到 Agent Skills 池。
- 修改 `global/AGENTS.md` 后发布；修改自有 Skill 后递增其版本并发布；第三方 Skill 只整目录更新并登记来源。
- 交付前运行与改动对应的检查、`python scripts/sync.py --check` 和 `git diff --check`。验证通过后自动创建一次仅含本次变更的中文本地提交，不推送。
