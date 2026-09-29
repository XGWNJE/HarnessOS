# HarnessOS

HarnessOS 把个人 AI 工作台中需要长期保留的规则、技能、流程和其他受管资产放在可审阅的事实源中，并从这些事实源生成浏览目录与恢复清单。登记资产由用户明确发起；仓库不会扫描工作站来推断要管理什么。

## 查看资产

在 Windows 上双击仓库根目录的 [catalog.html](catalog.html)，即可搜索、筛选并查看资产详情。需要纯文本索引时打开 [CATALOG.md](CATALOG.md)。这两个文件由脚本生成，不直接编辑。

已安装 Python 时，也可以在仓库根目录运行：

```powershell
python scripts/catalog.py list
python scripts/catalog.py list --type skill
```

命令按资产 ID 输出状态、时效性、来源性质、上游更新策略和名称；第二条只显示 Skill。要校验事实源、引用和生成目录，运行 `python scripts/catalog.py check`。

## 内容放在哪里

| 内容 | 事实源或入口 |
|---|---|
| 跨项目规则 | [global/AGENTS.md](global/AGENTS.md) |
| 自有 Skill | [skills/](skills/) |
| 第三方 Skill | [vendor/](vendor/)；引入来源见 [SOURCES.md](vendor/SOURCES.md) |
| Workflow | [workflows/](workflows/) |
| 资产记录、类型和配置档 | [inventory/](inventory/)；字段与生命周期见 [受管资产模型](inventory/README.md) |
| 生成的浏览目录 | [catalog.html](catalog.html) 和 [CATALOG.md](CATALOG.md) |

仓库保存可恢复的正文、索引和恢复配方；自有项目何时在 `archive/` 保存正文副本，按 [项目规则](AGENTS.md#自有资产入仓备份) 判定。仓库不保存安装包、账号、密钥、许可证正文或生产配置。

## 登记与恢复

登记新资产按 [登记受管资产](workflows/register-managed-asset.md) 进行。软件、开发工具等记录在 `inventory/assets/<type>/<slug>.toml`；Rule、Skill 和 Workflow 沿用各自的正文文件，不再建立重复的资产记录。

有目标配置档后，可用 `python scripts/catalog.py plan <profile>` 生成恢复清单；它只输出计划，不安装软件或恢复数据。实际迁移按 [恢复工作站](workflows/restore-workstation.md) 逐项核验。仓库目前没有配置档，执行 `plan` 前需按 [配置档格式](inventory/README.md#配置档与关系) 建立并校验。

维护命令、发布方式与操作边界集中在 [AGENTS.md](AGENTS.md)。
