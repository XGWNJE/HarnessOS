# HarnessOS 项目规则

本仓库只管理全局 `AGENTS.md` 与可复用 skills。

## 源与边界

- 全局规则源是 `global/AGENTS.md`；自有 skill 源是 `skills/`；第三方 skill 原样存放于 `vendor/`，来源与迁移条件登记在 `vendor/SOURCES.md`。
- 只能修改上述源文件，不能直接修改各 Agent 的发布目标。
- `vendor/` 不手工修补；上游更新时整目录替换。第三方 skill 的完整运行依赖必须随目录保留。
- 密钥、token、私钥和生产配置不得进入仓库。

## 发布与验证

| 用途 | 命令 |
|---|---|
| 发布全局 AGENTS 与全部 skill | `python scripts/sync.py` |
| 只检查发布漂移 | `python scripts/sync.py --check` |
| 单独发布全局 AGENTS | `python scripts/publish_global.py` |
| 单独发布全部 skill | `python scripts/publish_skills.py` |

- 改 `global/AGENTS.md` 后递增文件头版本并发布；改自有 skill 后递增其版本并发布。第三方 skill 只整目录更新并登记来源。
- 交付前运行 `python scripts/sync.py --check`；验证通过后自动提交一次，提交只包含本次变更。
