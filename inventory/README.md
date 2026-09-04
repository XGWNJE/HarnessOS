# 受管资产模型

本目录是 HarnessOS 受管资产的结构与字段说明。仓库统一管理资产的身份、关系、状态、索引与恢复入口，但不强迫不同资产共用同一种正文格式。

## 事实源与目录

- Rule 正文的唯一事实源是 `global/AGENTS.md`。
- Skill 正文及来源的唯一事实源是 `skills/` 与 `vendor/`。
- Workflow 的唯一事实源是 `workflows/<slug>.md`，使用 TOML frontmatter 携带公共字段。
- Software、Development Tool 及后续类型的唯一事实源是 `inventory/assets/<type>/<slug>.toml`。
- Profile 位于 `inventory/profiles/<slug>.toml`，只组合资产，不复制资产事实。
- `inventory/taxonomy.toml` 是类型、领域、状态、关系和配置档层级枚举的唯一事实源。

资产 ID 固定为 `<type>:<slug>`。文件名只使用 `slug`，不包含 Windows 文件名不支持的冒号。目录尚无真实资产或配置档时不创建空目录。

Rule 与 Skill 由目录生成器通过原生来源适配为统一索引：路径是 `fact_source`，Rule 使用全局规则文件身份，Skill 使用各自 frontmatter 和目录名。不要为它们建立重复的资产 TOML。

## 公共字段

非 Rule/Skill 资产记录至少包含以下字段：

```toml
schema_version = 1
id = "<type>:<slug>"
type = "<type>"
name = "人类可读名称"
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

[[relationships]]
type = "depends-on"
target = "另一资产的完整 ID"
```

- `status` 只取 `managed`、`excluded`、`retired`。后两者保留决策历史，但不进入恢复清单。
- `preference_source` 只描述偏好依据：用户明确声明、已核验的公开事实或未知。公开事实不能代替个人偏好。
- `provenance` 只取 `owner-produced`（用户自产）或 `third-party`（第三方）。Rule 与自有 Skill 由生成器自动标记为用户自产，`vendor/` 中的 Skill 自动标记为第三方；Workflow 和结构化资产在源记录中显式声明。
- `upstream_updates` 表示是否跟踪外部上游更新。用户自产资产没有外部上游，必须为 `false`，目录显示“不适用”；这不妨碍它在 Git 中继续修订和版本化。第三方资产可按实际维护策略填写 `true` 或 `false`。
- `current`、`stale`、`incomplete` 是根据日期和字段计算的展示状态，不写回源文件。
- `review_days` 默认 90 天，可按资产覆盖；执行真实迁移时即使记录仍新鲜，也要实时核验易变的版本、兼容性、来源和许可条件。
- 关系只引用资产 ID，不复制对方事实。`depends-on` 不得形成循环；目标不存在时校验失败。
- `fact_source`、配置引用和备份位置必须使用仓库相对路径或人能理解的逻辑位置，不保存机器绝对路径。
- 逻辑引用不能是 URL；公开官网放在对应类型的官方来源字段，私有分享链接不入库。

## 软件扩展

`software` 资产除公共字段外使用 `[software]`：

```toml
[software]
install_form = "portable"
release_channel = "lts"
minimum_verified_version = ""
pinned_version = ""
avoid_versions = []
official_source = "https://vendor.example/download"
config_restore = "逻辑恢复说明或 unknown"
backup_location = "网盘 / 工作台备份 / 工具名"
post_restore_checks = ["可观察的启动或功能验收"]
```

安装形态与发行通道使用 `taxonomy.toml` 枚举。空版本表示未固定，不等同于最新版；无法确认的偏好使用 `unknown`，不得自行猜测。

## 开发环境工具扩展

`development-tool` 用于版本控制、包管理器、编译器、Runtime/SDK 与通用 CLI。除公共字段外使用 `[development_tool]`：

```toml
[development_tool]
tool_kind = "cli"
commands = ["tool"]
install_source = "官方安装源或包管理器名称"
package_id = ""
version_constraint = ">=1.0"
update_channel = "stable"
environment_variables = ["VARIABLE_NAME"]
config_reference = "逻辑配置引用或 unknown"
verification_commands = ["tool --version"]
```

环境变量只记录名称和取值来源提示，不记录值。配置引用不能包含私有 registry token、认证信息或完整机器配置。依赖统一写在公共 `relationships` 中，不在扩展表重复维护。

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
- 可核验官网、支持版本、兼容性与最低要求等公开事实，但登记前仍需区分事实与偏好。
- 不做后台扫描、整机软件枚举、跨项目自动登记或定时巡检。
- 不保存安装包、完整配置、账号、密码、密钥、token、私钥、许可证正文、私有分享链接或机器绝对路径。
- 许可证只允许保存公开条款或用户自有凭据保管位置的逻辑引用，不能保存许可证密钥本身。

首次登记与恢复分别遵循 `workflows/register-managed-asset.md` 和 `workflows/restore-workstation.md`。恢复清单只提供决策与核验依据，不自动安装软件、连接服务或恢复数据。

生成恢复清单时，可重复传入 `--satisfied <asset-id>` 标记目标环境已经满足的资产；该状态只用于本次输出，不写回 Profile 或资产源。
