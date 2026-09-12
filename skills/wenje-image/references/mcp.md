# MCP 注册与排查

MCP 是首选入口：出图变成一次原生工具调用，不再需要写临时脚本、拼 shell 命令或手工轮询。

## 注册

```bash
python <本skill目录>/scripts/wenje_image.py install --agent zcode    # 或 codex / claude / all
python <本skill目录>/scripts/wenje_image.py install --print         # 只打印片段，不动文件
```

`install` 的行为：目标文件已存在才写；写入前在同一目录留一份 `.wenje-backup-<时间戳>` 备份；已有同名条目则不重复写。注册后**需重启 Agent** 才会出现工具。

各 Agent 的落点：

| Agent | 文件 | 位置 |
|---|---|---|
| ZCode | `~/.zcode/cli/config.json` | `mcp.servers.wenje-image` |
| Claude Code | `~/.claude.json` | `mcpServers.wenje-image` |
| Codex | `~/.codex/config.toml` | `[mcp_servers.wenje-image]` |

手工片段（ZCode / Claude 用 JSON，Codex 用 TOML）：

```json
{
  "mcpServers": {
    "wenje-image": {
      "type": "stdio",
      "command": "<python 解释器绝对路径>",
      "args": ["<本skill目录>/scripts/wenje_mcp.py"]
    }
  }
}
```

```toml
[mcp_servers.wenje-image]
command = "<python 解释器绝对路径>"
args = ["<本skill目录>/scripts/wenje_mcp.py"]
```

`command` 用解释器绝对路径而不是 `python`：Agent 启动 MCP 时的 PATH 不一定与终端一致。

## 边界

MCP 注册是**每台机器的本地动作**，不在 HarnessOS 仓库的发布流水线内——流水线只发布 skill 目录本身。换机恢复时，恢复 skill 后要重跑一次 `install`。

## 排查

| 现象 | 原因 | 处置 |
|---|---|---|
| 工具列表里没有 `generate_image` | 未注册，或注册后没重启 Agent | 重跑 `install`，重启 Agent；用 `install --print` 核对片段 |
| Agent 报 MCP server 启动失败 | `command` 指向的解释器不存在，或脚本路径变更 | 用 `install` 重写（会自动指向当前解释器与脚本）；确认 `python <脚本> --version` 能打印版本 |
| 工具出现但调用报"未配置密钥" | 还没录入密钥 | 调 `open_setup_page`，由用户在浏览器里填 |
| 换了 Python 环境后失效 | 解释器路径变了 | 重跑 `install`（先删除旧条目或直接覆盖写入） |
| 想彻底移除 | — | 从对应配置文件中删掉 `wenje-image` 条目并重启 Agent |

设置页相关问题：`open_setup_page` 只监听 `127.0.0.1` 的随机端口，页面带一次性路径令牌与 CSRF 校验，保存成功即自行退出；浏览器没自动弹出时，把返回的 URL 手动打开即可（`no_browser` 参数可只返回 URL）。
