# 受管资产模型

本目录是 HarnessOS 受管资产的结构与字段说明。仓库统一管理资产的身份、关系、状态、索引与恢复入口，但不强迫不同资产共用同一种正文格式。

## 事实源与目录

- Rule 正文的唯一事实源是 `global/AGENTS.md`。
- Skill 正文及来源的唯一事实源是 `skills/` 与 `vendor/`。
- Workflow 的唯一事实源是 `workflows/<slug>.md`，使用 TOML frontmatter 携带公共字段。
- 软件、开发工具及后续类型的唯一事实源是 `inventory/assets/<type>/<slug>.toml`。
- Profile 位于 `inventory/profiles/<slug>.toml`，只组合资产，不复制资产事实。
- `inventory/taxonomy.toml` 是类型、领域、状态、关系和配置档层级枚举的唯一事实源。

类型演进遵循增量优先：新内容能在现有类型语义和扩展字段内表达时直接新增字段或记录；只有语义边界、生命周期或恢复方式发生不兼容变化时才新增或重构类型。主线程根据事实自动判断，并在记录或交付中说明依据。

资产 ID 固定为 `<type>:<slug>`。文件名只使用 `slug`，不包含 Windows 文件名不支持的冒号。目录尚无真实资产或配置档时不创建空目录。

Rule 与 Skill 由目录生成器通过原生来源适配为统一索引：路径是 `fact_source`，Rule 使用全局规则文件身份，Skill 使用各自 frontmatter 和目录名。不要为它们建立重复的资产 TOML。

## 公共字段

非 Rule/Skill 资产统一使用以下词条模板，不再为每种类型另设字段集；字段不适用时省略，缺少可选字段不视为错误：

```toml
schema_version = 1
id = "<type>:<slug>"
type = "<type>"
name = "产品官方名（中文资产用官方中文名）"
domain = "taxonomy.toml 中的领域 ID"
status = "managed"
purpose = "为何纳管，以及恢复后解决什么问题"
platforms = ["windows"]
fact_source = "当前事实源的仓库相对路径"
preference_source = "owner-declared"
provenance = "owner-produced"
upstream_updates = false
declared_on = "YYYY-MM-DD"
last_verified_on = "YYYY-MM-DD"
review_days = 90
notes = ""

# 形态与安装
tool_kind = ""                                # 开发工具类型枚举；非开发工具留空
install_form = ""                             # 软件安装形态枚举；非软件留空
commands = []                                 # 主要命令
install_source = ""                           # 安装来源：包管理器名称或官方安装源
official_source = ""                          # 官方来源 URL
package_id = ""                               # 渠道包 ID（WinGet / npm / 商店等）

# 版本与渠道
version_constraint = ""                       # 版本约束表达式
release_channel = ""                          # 发行/更新渠道枚举（software 发行通道与 development-tool 更新通道共用此字段）
minimum_verified_version = ""                 # 已核验的最低本机版本
pinned_version = ""
avoid_versions = []

# 配置、恢复与核验
environment_variables = []                    # 只记录名称与取值来源提示，不记录值
config_reference = ""                         # 配置恢复说明或逻辑引用（software 原 config_restore 并入此字段）
backup_location = ""                          # 备份位置逻辑引用
verification_commands = []
post_restore_checks = []

# 上游查询渠道
upstream_channel = ""                         # taxonomy.toml 的 upstream_channels 枚举
upstream_identifier = ""                      # 包 ID / 包名 / owner-repo / 商店产品 ID / 官方 URL / 逻辑引用
upstream_latest_stable = ""                   # 上次核验时该渠道返回的最新稳定版本
upstream_pending_channel = ""                 # 已批准的待切换渠道，本次不生效
upstream_pending_identifier = ""
upstream_pending_note = ""                    # 渠道切换的生效条件

[[relationships]]
type = "depends-on"
target = "另一资产的完整 ID"
```

- `domain` 判定口径：类型按形态划分（命令行工具、SDK 与运行时归 development-tool，桌面应用与游戏归 software）；领域按资产服务的主要场景归入唯一领域——development-tool 统一归 `development`，software 及后续类型按主要使用场景选择领域，场景并列时取主用途，不按次要能力叠加。
- `tool_kind`、`install_form`、`release_channel` 取 `taxonomy.toml` 枚举；`release_channel` 统一承载原 software 发行通道与 development-tool 更新通道语义。
- 类型必填字段（缺失或 `unknown` 时目录标为 incomplete）：`software` 必填 `install_form`、`release_channel`、`official_source`、`minimum_verified_version`；`development-tool` 必填 `tool_kind`、`commands`、`install_source`、`version_constraint`、`verification_commands`。其余字段按适用性填写，不适用时省略。
- 空版本只表示用户明确不固定版本；实际版本未知时记录不完整，不能用空值代替核验；用户尚未决定的个人偏好才可使用 `unknown`，不得自行猜测。
- `status` 只取 `managed`、`excluded`、`retired`。后两者保留决策历史，但不进入恢复清单。
- `preference_source` 只描述偏好依据：用户明确声明、已核验的公开事实或未知。公开事实不能代替个人偏好。
- `provenance` 只取 `owner-produced`（用户自产）或 `third-party`（第三方）。Rule 与自有 Skill 由生成器自动标记为用户自产，`vendor/` 中的 Skill 自动标记为第三方；Workflow 和结构化资产在源记录中显式声明。
- `upstream_updates` 表示是否跟踪外部上游更新。用户自产资产没有外部上游，必须为 `false`，目录显示“不适用”；这不妨碍它在 Git 中继续修订和版本化。第三方资产可按实际维护策略填写 `true` 或 `false`。
- `current`、`stale`、`incomplete` 是根据日期和字段计算的展示状态，不写回源文件。
- `review_days` 默认 90 天，可按资产覆盖；执行真实迁移时即使记录仍新鲜，也要实时核验易变的版本、兼容性、来源和许可条件。
- 配置引用不能包含私有 registry token、认证信息或完整机器配置。
- 关系只引用资产 ID，不复制对方事实。`depends-on` 不得形成循环；目标不存在时校验失败。
- `fact_source`、配置引用和备份位置必须使用仓库相对路径或人能理解的逻辑位置，不保存机器绝对路径。
- 逻辑引用不能是 URL；公开官网放在对应类型的官方来源字段，私有分享链接不入库。

## 上游查询渠道

跟踪上游更新的资产用 `upstream_*` 字段登记查询渠道，供 `python scripts/versions.py` 批量核验：

```toml
upstream_channel = "winget"                 # taxonomy.toml 的 upstream_channels 枚举
upstream_identifier = "Git.Git"             # 包 ID / 包名 / owner-repo / 商店产品 ID / 官方 URL / 逻辑引用
upstream_latest_stable = "2.55.0.3"         # 上次核验时该渠道返回的最新稳定版本

# 已批准的渠道切换先登记为待生效，不改变当前查询渠道：
upstream_pending_channel = "official-api"
upstream_pending_identifier = "https://dl.google.com/android/repository/repository2-3.xml"
upstream_pending_note = "下次版本更新时先核验新渠道口径与现渠道一致后生效"
```

- `upstream_channel` 与 `upstream_pending_channel` 取 `taxonomy.toml` 的 `upstream_channels` 枚举。`unavailable` 表示未找到可核验的上游更新渠道，此时不填定位符与 `upstream_latest_stable`，并在 notes 说明原因；`launcher` 表示版本由本机启动器或应用内更新托管，以本机配置为版本证据。
- 渠道切换流程：先登记 `upstream_pending_*` 与生效条件；`versions.py` 或人工核验新渠道口径一致后，在下一次版本更新时把 `upstream_pending_channel` 提升为 `upstream_channel` 并清空 pending 字段。不得用未核验的渠道值覆盖版本事实。
- 低算力维护顺序：先运行 `python scripts/versions.py`（每资产至多一次请求，只读）；winget/npm/PyPI/GitHub Releases/Store/官方接口渠道零人工完成，`official-page` 渠道才需人工查看网页，`launcher` 以本机启动器配置为准，`unavailable` 等待渠道决策。核验后同步更新 `upstream_latest_stable` 与 notes，并刷新 `last_verified_on`。
- `upstream_latest_stable` 只记录渠道口径的版本号；渠道显示格式与上游命名不同（如 winget 包版本、商店包版本）时以渠道实际返回为准，在 notes 说明对应关系。

## 配置档与关系

Profile 描述目标环境，不是软件清单副本：

```toml
schema_version = 1
id = "main-workstation"
name = "主力工作站"
description = "目标环境说明"
platforms = ["windows"]
last_verified_on = "YYYY-MM-DD"
review_days = 90

[[assets]]
id = "software:example"
tier = "required"
notes = "仅记录本配置档中的必要说明"
```

`tier` 只取 `required`、`standard`、`optional`。Profile 不覆盖安装偏好、版本策略或事实源；需要改变这些事实时修改资产记录。Profile 必须显式包含所选资产的全部 `depends-on` 依赖，缺少时校验直接失败，不生成看似完整的恢复清单。关系类型的含义如下：

- `depends-on`：缺少目标资产时本资产不可用。
- `uses`：运行或执行时会使用目标资产。
- `replaces`：本资产是目标资产的替代选择。
- `backs-up-to`：目标资产承载其备份；具体位置仍只写逻辑引用。
- `published-to`：本资产由流水线发布到目标资产代表的运行环境或服务。

## 登记与安全边界

- 只有用户明确要求“登记”“纳管”或“更新”某项资产时，才能新增或修改正式记录。
- 安装形态、版本通道、主要用途、恢复范围等个人偏好必须来自用户确认；不得由已安装软件扫描、普通对话或公开资料推断。
- 可核验官网、支持版本、兼容性与最低要求等公开事实；关键事实未完成深度核验时暂不创建正式记录。
- `unknown` 只表示用户尚未决定的偏好或已明确标记的历史缺口，不能代替来源调查或登记前核验。
- 不做后台扫描、整机软件枚举、跨项目自动登记或定时巡检。
- 不保存安装包、完整配置、账号、密码、密钥、token、私钥、许可证正文、私有分享链接或机器绝对路径。
- 许可证只允许保存公开条款或用户自有凭据保管位置的逻辑引用，不能保存许可证密钥本身。
- 自有项目是否把正文备份进本仓库，按 `AGENTS.md` 的「自有资产入仓备份」判定；正文副本放 `archive/<slug>/`，资产身份、字段与生命周期仍只以本目录为准。

首次登记与恢复分别遵循 `workflows/register-managed-asset.md` 和 `workflows/restore-workstation.md`。恢复清单只提供决策与核验依据，不自动安装软件、连接服务或恢复数据。

生成恢复清单时，可重复传入 `--satisfied <asset-id>` 标记目标环境已经满足的资产；该状态只用于本次输出，不写回 Profile 或资产源。
