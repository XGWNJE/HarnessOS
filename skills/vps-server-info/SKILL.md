---
version: 1.0.0
name: vps-server-info
description: VPS 服务器连接信息（IP/端口/SSH/部署路径）。当项目需要 SSH 连接 VPS、部署 server、查询服务器配置时使用。
---

# VPS 服务器信息

> 全局技能。用于获取当前默认 VPS 的连接方式、服务分工、部署路径和只读核验命令。涉及发布、重启、证书、Nginx 改动前，必须先做实时核验，不要只依赖本文档。

## 最近核验

- 核验时间：2026-05-25（Asia/Shanghai）
- 核验方式：读取本机 `C:\Users\Administrator\.ssh\config`，并通过 SSH 在 VPS 上执行只读检查
- 当前默认 SSH 别名：`xgwnje`
- 兼容旧别名：`visionguard`

## SSH 连接

本机 SSH config 当前配置：

```sshconfig
Host xgwnje visionguard
  HostName 216.36.111.208
  Port 53111
  User root
  IdentityFile ~/.ssh/id_ed25519
```

常用命令：

```bash
ssh xgwnje                             # 登录默认 VPS
ssh xgwnje "uptime"                    # 远程执行只读命令
scp file.txt xgwnje:/opt/visionguard/  # 上传文件示例
```

在 Codex sandbox 中如果 `ssh xgwnje` 报 “Could not resolve hostname xgwnje”，通常是 sandbox 没读到用户 SSH config。可显式指定配置文件：

```powershell
ssh -F C:\Users\Administrator\.ssh\config xgwnje "uptime"
```

## 服务器基本信息

| 项目 | 当前值 |
|---|---|
| 主机名 | `C202604291716769` |
| 系统 | Debian GNU/Linux 12 (bookworm) |
| Kernel | `6.1.0-10-amd64` |
| CPU | 2 vCPU |
| 内存 | 1.9 GiB，无 swap |
| 根分区 | `/dev/vda1`，40G，总使用约 5.5G（2026-05-25 核验） |
| 公网 IP / SSH | `216.36.111.208:53111` |

供应商规格历史记录：2×E5v4、2G DDR4、40G SSD、200M 上 / 100M 下、月流量 2000G。该规格来自旧记录，若涉及采购/续费请重新到面板核验。

## 当前服务分工

| 域名 / 地址 | 当前用途 | 后端 / 路径 | 核验结果 |
|---|---|---|---|
| `https://xgwnje.cn` | WebHome 主页 | Nginx 静态站点 `/var/www/webhome/current` | `200` |
| `https://www.xgwnje.cn` | WebHome 主页别名 | 同上 | 未单独核验，Nginx 已配置 |
| `https://visionguard.xgwnje.cn` | VisionGuard API / WebSocket | Nginx 反代 `127.0.0.1:3000` | `/health` 返回 `200` |
| `wss://visionguard.xgwnje.cn/ws` | VisionGuard WebSocket | Nginx 反代 `127.0.0.1:3000/ws` | Nginx 已配置 |
| `https://status.xgwnje.cn` | Uptime Kuma 状态页 | Docker 暴露 `127.0.0.1:3001` | 返回 `401`，Basic Auth 预期行为 |

注意：旧文档里的 `https://xgwnje.cn` 作为 VisionGuard 主服务域名已经过时。根域现在是 WebHome；VisionGuard 当前应优先使用 `visionguard.xgwnje.cn`。

## VisionGuard 部署

| 项目 | 当前值 |
|---|---|
| 服务名 | `visionguard.service` |
| systemd 文件 | `/etc/systemd/system/visionguard.service` |
| 运行用户 | `visionguard` |
| 工作目录 | `/opt/visionguard/VisionGuard_Server` |
| 启动命令 | `/usr/bin/node dist/index.js` |
| Node 端口 | `3000` |
| Nginx 站点 | `/etc/nginx/sites-enabled/visionguard.xgwnje.cn` |
| 健康检查 | `curl -ksS https://visionguard.xgwnje.cn/health` |
| API Key 变量 | `VISIONGUARD_API_KEY` / server `.env` 中的 `API_KEY`，不要在公开文档或提交中写明文 |

常用只读检查：

```bash
ssh xgwnje "systemctl status visionguard --no-pager -l | sed -n '1,30p'"
ssh xgwnje "systemctl is-active visionguard nginx docker"
ssh xgwnje "curl -ksS -o /dev/null -w '%{http_code}\n' https://visionguard.xgwnje.cn/health"
ssh xgwnje "ss -tlnp | grep -E ':(3000|3001|80|443) ' || true"
```

部署命令仍以 VisionGuard 仓库内脚本为准，执行前先确认当前 checkout 和脚本内容：

```bash
cd VisionGuard
bash server/deploy.sh          # 常规部署，具体行为以脚本当前内容为准
bash server/deploy.sh --full   # 含依赖，执行前必须确认影响范围
bash server/deploy.sh --nginx  # 涉及 Nginx，执行前必须核验站点分工
```

## WebHome 部署

| 项目 | 当前值 |
|---|---|
| 根域 | `https://xgwnje.cn` / `https://www.xgwnje.cn` |
| 服务器路径 | `/var/www/webhome` |
| 当前发布 symlink | `/var/www/webhome/current -> /var/www/webhome/releases/20260521-094839`（2026-05-25 核验） |
| Nginx 站点 | `/etc/nginx/sites-enabled/xgwnje.cn` |

WebHome 发布应使用 release 目录 + `current` symlink 的方式，发布后从 VPS 侧用 `curl` 验证根域 HTTP 状态。

## Uptime Kuma / 状态页

| 项目 | 当前值 |
|---|---|
| 域名 | `https://status.xgwnje.cn` |
| 后端 | `127.0.0.1:3001` |
| 运行方式 | Docker / docker-proxy |
| 访问控制 | Nginx Basic Auth，配置文件 `/etc/nginx/.htpasswd-status` |
| Nginx 站点 | `/etc/nginx/sites-enabled/status.xgwnje.cn` |

`status.xgwnje.cn` 返回 `401` 不代表服务异常；这是 Basic Auth 的预期结果。

## 密钥和敏感信息边界

| 项目 | 路径 / 说明 |
|---|---|
| SSH 私钥 | `~/.ssh/id_ed25519` |
| SSH 公钥历史路径 | `D:\ObjectCode\vps-proxies\instance\ssh-public-key.pub` |
| VPS 配置历史路径 | `D:\ObjectCode\vps-proxies\instance\vps-config` |
| 代理配置历史路径 | `D:\ObjectCode\vps-proxies\instance\proxies-hybrid.yaml` |
| VisionGuard API Key | 使用环境变量 / server `.env`，不要写进仓库、PR、公开文档或聊天总结 |

涉及密钥、Reality 参数、代理节点、证书私钥时，只能读取必要状态，不要把明文复制进输出或提交。

## 其他历史记录

| 用途 | IP | 状态 |
|---|---|---|
| 数据中心 VPS（非 AI 流量） | `66.154.112.91` | 旧记录，本轮未核验；不要作为默认目标 |

## 核验参考命令

```powershell
ssh -F C:\Users\Administrator\.ssh\config xgwnje "hostname; uptime; free -h; df -h /"
ssh -F C:\Users\Administrator\.ssh\config xgwnje "systemctl is-active nginx visionguard docker"
ssh -F C:\Users\Administrator\.ssh\config xgwnje "curl -ksS -o /dev/null -w 'root %{http_code}\n' https://xgwnje.cn/; curl -ksS -o /dev/null -w 'vg %{http_code}\n' https://visionguard.xgwnje.cn/health; curl -ksS -o /dev/null -w 'status %{http_code}\n' https://status.xgwnje.cn/"
```
