# HarnessOS 项目规则

本仓库是个人 AI 工作台的轻量受管资产中枢，管理资产索引、恢复配方以及 Rules 与 Skills 的既有发布链。

## 源与边界

- `global/AGENTS.md` 是跨项目 Rule 正文的事实源；`skills/` 是自有 Skill 的事实源；`vendor/` 是第三方 Skill 的受管副本（默认保持上游原样，允许按下述规则携带本地补丁）；`workflows/` 是 Workflow 正文的事实源；`inventory/` 管理资产分类、结构化资产记录与工作台配置档。
- `catalog.html` 与 `CATALOG.md` 是从同一事实源生成的快速浏览页和精简文本索引，均不手工修改；不能直接修改各 Agent 的 Rules 或 Skills 发布目标。
- `vendor/` 默认不手工修补；用户明确授权后可维护必要的本地补丁，但必须在 `vendor/SOURCES.md` 登记上游提交、修改原因、差异范围、验证结果以及补丁移除或重放条件，不得把补丁版表述为上游原版。上游更新时先核对本地补丁是否已被吸收：已吸收则整目录替换并移除补丁记录，未吸收则基于新上游重新验证和重放；不得用上游更新静默覆盖本地差异。第三方 Skill 的许可证、完整运行依赖与补丁所需测试必须随目录保留。
- 仓库只保存索引和恢复配方，不保存安装包、完整配置、账号、许可证正文、密钥、token、私钥、私有分享链接、生产配置或机器绝对路径。备份位置使用不含凭据的逻辑引用。
- 只有用户明确要求登记、纳管或更新某项资产时，才能探索并写入对应记录；不得主动扫描已安装软件、枚举整机环境、从普通对话推断个人偏好或设置后台巡检。
- 软件安装形态、版本通道、主要用途和恢复范围等偏好由用户确认；动态事实在真实迁移前重新核验官方来源、兼容性、支持版本与许可条件。
- 资产字段、上游渠道、类型演进、关系与生命周期统一遵循 `inventory/README.md`；不要在本文件复制字段规则。

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
- 修改 `global/AGENTS.md` 后发布；修改自有 Skill 后递增其版本并发布；第三方 Skill 的上游更新采用整目录替换，本地补丁仅在用户明确授权后应用，并同步更新 `vendor/SOURCES.md` 的差异与验证记录。
- 交付前运行与改动对应的检查、`python scripts/sync.py --check` 和 `git diff --check`。验证通过后自动创建一次仅含本次变更的中文本地提交，不推送。

## 自有资产入仓备份

自有资产（`owner-produced`）在**没有独立远端仓库**时，本仓库就是它唯一的可恢复副本。是否把正文放进本仓库按下面的档位判定：

| 情形 | 处置 |
|---|---|
| Rule / 自有 Skill / Workflow | 正文本来就在 `global/`、`skills/`、`workflows/`，仓库即备份，不再另建副本 |
| 自有项目，无独立远端仓库，正文 ≤ 50 MB | 登记时把正文复制到 `archive/<slug>/`，资产记录的 `backup_location` 写 `archive/<slug>/` |
| 自有项目，正文 > 50 MB | 不入库；登记逻辑引用与不入库原因，异机备份由用户另行安排 |
| 自有项目，剔除凭据后仍无法脱敏 | 不入库，处置同上 |
| 已有独立远端仓库 | 不复制进本仓库，只在资产记录里登记该远端的逻辑引用 |

- 50 MB 是**单个项目正文的总体积**上限：与 GitHub 单文件 50 MiB 警告线同一数量级，给单文件 100 MiB 硬限留足余量。
- 入库内容仍受「源与边界」约束：剔除密钥、token、私钥、`.env`、许可证正文、生产配置与私有分享链接；只备份正文（源码、文档、模板），不备份安装包与构建产物。
- `archive/` 只是正文副本存放处：不参与 `catalog.py` 的资产扫描，也不进入发布流水线；资产身份、字段与生命周期仍然只在 `inventory/` 里维护。
- 更新时整目录替换 `archive/<slug>/` 并记录版本与日期；没有符合条件的资产时不预先创建空目录。
