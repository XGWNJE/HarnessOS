+++
schema_version = 1
id = "workflow:restore-workstation"
type = "workflow"
name = "恢复工作站"
domain = "system-hardware"
status = "managed"
purpose = "依据已确认的资产与配置档，生成并验收一套符合用户习惯的工作站。"
platforms = ["windows"]
fact_source = "workflows/restore-workstation.md"
preference_source = "owner-declared"
provenance = "owner-produced"
upstream_updates = false
declared_on = "2026-09-04"
last_verified_on = "2026-09-04"
review_days = 90
notes = "首版 Windows 优先；本流程不授权自动安装、登录或恢复数据。"
relationships = []
+++

# 恢复工作站

## 目标

基于指定 Profile 和受管资产生成轻量、可核验的恢复清单，使新工作站达到用户确认的最低可用状态，并明确哪些内容不恢复或仍需决定。

## 触发条件

用户明确要求规划或执行工作站迁移、重装或恢复，并指定目标 Profile；实际安装、登录、下载私有内容或恢复数据仍需相应授权。

## 输入

- 目标 Profile、操作系统与目标机器约束。
- 当前机器已经满足的资产及可验证版本。
- 资产来源性质、上游更新策略、依赖、安装偏好、版本策略、逻辑备份位置与恢复后验收项。
- 用户允许执行的范围，以及账号、许可证和私有备份由谁提供。

## 人工确认点

- 确认目标 Profile，以及 `required`、`standard`、`optional` 三档的本次恢复范围。
- 对 `unknown`、`stale`、固定旧版本、来源变化、兼容性冲突和许可证要求作出决定。
- 下载、安装、登录、连接服务、写入配置或恢复数据前，确认对应操作已获授权。
- 对 `excluded` 与 `retired` 资产保持不恢复，除非用户明确改变其生命周期状态。

## 失败边界

- 恢复计划只生成清单，不自动安装软件、连接服务、登录账号或恢复数据。
- 用户自产资产按仓库内受管事实源恢复，不把仓库修订误称为上游更新；仅对标记为跟踪上游的第三方资产核验新版本。
- 仓库记录不是“当前最新版”的证明；第三方资产迁移时仍要实时核验官方来源、支持版本、兼容性与许可条件。
- 缺少关键字段、备份不可访问、依赖悬空或依赖循环时停止受影响分支，并归入“需要决定”。
- 不使用仓库中的逻辑引用猜测凭据、许可证密钥、私有链接或本机路径。

## 验收证据

- 清单分为“需要恢复、已经满足、可选、明确不恢复、需要决定、信息过期”。
- 恢复顺序满足 `depends-on` 关系，同一资产不会因被多个 Profile 引用而重复安装。
- 每项恢复资产通过其版本检查与功能验收；失败项、跳过项和偏差均可追溯。
- 最终环境满足目标 Profile 的必需项，未越过用户授权范围，且没有把敏感数据写回仓库。
