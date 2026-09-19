# MCP 注册与排查

MCP 是首选入口：出图变成一次原生工具调用，不再需要写临时脚本、拼 shell 命令或手工轮询。

## 注册

```bash
python <本skill目录>/scripts/wenje_image.py install --agent all    # 或 claude / codex / zcode / dsh
python <本skill目录>/scripts/wenje_image.py install --print        # 只打印片段，不动文件
```

`install` 的行为：目标文件已存在才写，本机没有的配置文件直接跳过；写入前在同一目录留一份 `.wenje-backup-<时间戳>` 备份。已有同名条目时按内容判断——内容与当前写法一致就报「已存在」且不碰文件，字段过期（例如早期版本没写超时）则整块替换。DSH 保存后热应用补丁层，其余 Agent 需重启。

## 各 Agent 的落点

| Agent | 文件 | 位置 | 工具全名 |
|---|---|---|---|
| Claude Code | `~/.claude.json` | `mcpServers.wenje-image` | `mcp__wenje-image__generate_image` |
| ZCode | `~/.zcode/cli/config.json` | `mcp.servers.wenje-image` | `mcp__wenje-image__generate_image` |
| Codex | `~/.codex/config.toml` | `[mcp_servers.wenje-image]` | `mcp__wenje-image__generate_image` |
| DSH | `~/.dsh/profiles/<profile>/cordis.patch.yml` | 补丁层里的 `- insert:` 条目（内含 `mcp-wenje-image`） | `mcp__wenje-image__generate_image` |

四家都会给工具加服务器名前缀，所以别用精确全名判断"注册没成功"——按 `generate_image` 搜。

DSH 的 `<profile>` 默认 `web`（即 `dsh web` 用的 profile），用 `--dsh-profile <名>` 改；一个 profile 一个补丁文件，注册进哪个 profile 就只有那个 profile 看得到工具。

## 手工片段

Claude Code / ZCode（JSON）：

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

Codex（TOML）：

```toml
[mcp_servers.wenje-image]
command = "<python 解释器绝对路径>"
args = ["<本skill目录>/scripts/wenje_mcp.py"]
tool_timeout_sec = 360
startup_timeout_sec = 30
```

DSH（YAML，追加到 `cordis.patch.yml`；`@deepseek-ai/dsh-mcp-client` 已随 DSH 的 profile 依赖装好，不用另装）：

```yaml
- insert:
    - id: mcp-wenje-image
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: wenje-image
        transport: stdio
        command: '<python 解释器绝对路径>'
        args: ['<本skill目录>/scripts/wenje_mcp.py']
        toolCallTimeoutMs: 360000
```

DSH 的补丁层是**按 id 定向**的：顶层写 `- id: <已有条目>` 表示覆盖或禁用那个条目，指向不存在的 id 会报 `patch: entry ... not found`；要新增插件必须像上面这样写 `- insert:`（不带 id 时插入到顶层数组，带 id 时插入到那个 group 条目的 `config` 里）。

DSH 还会清洗 stdio 子进程的环境——删掉名字里含 `KEY`/`PASSWORD`/`SECRET`/`TOKEN` 的变量以及所有 `DSH_*`。因此密钥要走 skill 自己的配置文件（`setup` / `open_setup_page` 写入的 `~/.wenje-image/config.json`），不要只依赖 `GRSAI_API_KEY` 环境变量。

## 调用超时

一次出图包含提交、轮询与下载，默认最长 300 秒。多数 Agent 的工具超时默认在 60 秒量级，不显式放宽就会在出图中途掐断调用：

| Agent | 字段 | 值 |
|---|---|---|
| Codex | `tool_timeout_sec` | 360 |
| DSH | `toolCallTimeoutMs`（毫秒） | 360000 |

Claude Code 的每服务器超时字段名未在本机核实，因此不写；若出现调用被掐断，用它的环境变量 `MCP_TOOL_TIMEOUT`（毫秒）覆盖。

## 边界

MCP 注册是**每台机器的本地动作**，不在 HarnessOS 仓库的发布流水线内——流水线只发布 skill 目录本身（发布进 `.agents` / `.codex` / `.claude` / `.dsh` 四个技能池，不碰任何 Agent 的 MCP 配置）。换机恢复时，恢复 skill 后要重跑一次 `install`。

## 排查

| 现象 | 原因 | 处置 |
|---|---|---|
| 工具列表里没有 `generate_image` | 未注册，或注册后没重启 Agent | 重跑 `install`，重启 Agent；用 `install --print` 核对片段 |
| Agent 报 MCP server 启动失败 | `command` 指向的解释器不存在，或脚本路径变更 | 用 `install` 重写（会自动指向当前解释器与脚本）；确认 `python <脚本> --version` 能打印版本 |
| 工具出现但调用报"未配置密钥" | 还没录入密钥，或只设了 `GRSAI_API_KEY` 而 DSH 把它清洗掉了 | 调 `open_setup_page`，由用户在浏览器里填；DSH 下必须走配置文件 |
| 调用到一半被取消 / 报超时 | 工具超时小于出图耗时 | 重跑 `install` 升级条目（会写入超时字段）；或把调用方的超时提到 360 秒以上 |
| 换了 Python 环境后失效 | 解释器路径变了 | 重跑 `install`（已有条目会整块替换） |
| DSH 启动或 `--dump-config` 报 `patch: entry ... not found` | 条目写成了顶层 `- id:`（那是覆盖已有条目的写法） | 重跑 `install`，它会整块替换成 `- insert:` 写法 |
| DSH 里没出现工具 | profile 选错（注册写进了别的 profile），或补丁层没保存 | 用 `--dsh-profile` 指定正在用的 profile 后重跑；确认 `cordis.patch.yml` 里有含 `mcp-wenje-image` 的 `- insert:` 条目 |
| 想彻底移除 | — | 从对应配置里删掉 `wenje-image` 条目（DSH 删含 `mcp-wenje-image` 的整个 `- insert:` 块），再重启 Agent |

设置页相关问题：`open_setup_page` 只监听 `127.0.0.1` 的随机端口，页面带一次性路径令牌与 CSRF 校验，保存成功即自行退出；浏览器没自动弹出时，把返回的 URL 手动打开即可（`no_browser` 参数可只返回 URL）。
