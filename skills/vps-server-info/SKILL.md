---
version: 1.1.1
name: vps-server-info
description: VPS 服务器连接信息（IP/端口/SSH/部署路径）。当项目需要 SSH 连接 VPS、部署 server、查询服务器配置时使用。
---

# VPS 服务器信息

> 全局技能（事实档案）。用于获取当前默认 VPS 的连接方式、服务分工、部署路径和只读核验命令。涉及发布、重启、证书、Nginx 改动前，必须先做实时核验，不要只依赖本文档。

## 最近核验

- 核验时间：2026-07-24（Asia/Shanghai）
- 核验方式：读取本机 `C:\Users\Administrator\.ssh\config`，并通过 SSH 在 VPS 上执行只读检查
- 当前默认 SSH 别名：`xgwnje`
- 兼容旧别名：`visionguard`
- **重要变更**：2026-06-29 前后 VPS 更换过新机器（主机名 `C202604291716769` → `C20260629016451`），2026-05-25 之前的记录（webhome 路径、Uptime Kuma、Basic Auth 状态页、Docker）全部作废

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
scp file.txt xgwnje:/var/www/          # 上传文件示例
```

在 Codex sandbox 中如果 `ssh xgwnje` 报 “Could not resolve hostname xgwnje”，通常是 sandbox 没读到用户 SSH config。可显式指定配置文件：

```powershell
ssh -F C:\Users\Administrator\.ssh\config xgwnje "uptime"
```

## 服务器基本信息

| 项目 | 当前值（2026-07-24 核验） |
|---|---|
| 主机名 | `C20260629016451` |
| 系统 | Debian GNU/Linux 12 (bookworm) |
| Kernel | `6.8.0-48-generic` |
| CPU | 1 vCPU |
| 内存 | 961 MiB，无 swap |
| 根分区 | `/dev/vda1`，20G，已用 11G（54%） |
| 公网 IP / SSH | `216.36.111.208:53111` |

规格比旧机（2 vCPU / 1.9G / 40G）缩水，部署新服务前先确认资源余量。

## Nginx 架构

配置文件在 `/etc/nginx/conf.d/`（不再是 sites-enabled）：

- `xgwnje-web-9443.conf`：主配置。外层 443 按域名分流到本机 `127.0.0.1:9443` 的各 per-host SSL server，再分别 root 到静态目录或反代后端
- `xgwnje-acme.conf`：`/.well-known/acme-challenge/` → `/var/www/acme`（证书签发）
- `xgwnje-mobile-subscription.conf`：`sub.xgwnje.cn` 订阅服务（有多个 .bak 备份，改动前先核对当前生效内容）

## 当前服务分工（2026-07-24 核验）

| 域名 | 当前用途 | 后端 / 路径 | 核验结果 |
|---|---|---|---|
| `xgwnje.cn` / `www.xgwnje.cn` | 主页 | 静态 `/var/www/xgwnje-home` | `200` |
| `m.xgwnje.cn` | 移动版 | 静态 `/var/www/xgwnje-mobile` | Nginx 已配置 |
| `api.xgwnje.cn` | 主页 API | 反代 `127.0.0.1:8787`（node `src/server.js`，工作目录 `/opt/homepage-api/releases/…`，release 制） | 进程在跑 |
| `status.xgwnje.cn` | 状态页 | 静态 `/var/www/xgwnje-status` | `200`（**不再是** Uptime Kuma，无 Basic Auth，Docker 已停用） |
| `visionguard.xgwnje.cn` | VisionGuard API / WebSocket | 反代 `127.0.0.1:3000` | `/health` 返回 `200` |
| `mail.xgwnje.cn` | 预留 | 静态 `/var/www/xgwnje-mail`（health 返回 "mail reserved"） | Nginx 已配置 |
| `sub.xgwnje.cn` | 订阅 | 见 `xgwnje-mobile-subscription.conf` | 未单独核验 |

注意：旧文档中的 `webhome/current` symlink 结构、Uptime Kuma（`127.0.0.1:3001`）、status 页 401 Basic Auth 均已不存在。`/var/www/` 下大量 `xgwnje-home.backup-*` 是发布系统产生的备份，清理前先确认发布脚本依赖。

## VisionGuard 部署

| 项目 | 当前值（2026-07-24 核验） |
|---|---|
| 服务名 | `visionguard.service`（enabled，active） |
| systemd 文件 | `/etc/systemd/system/visionguard.service` |
| 工作目录 | `/opt/visionguard-server`（**不再是** `/opt/visionguard/VisionGuard_Server`） |
| 启动命令 | `/usr/bin/node dist/index.js` |
| Node 端口 | `127.0.0.1:3000` |
| 健康检查 | `curl -ksS https://visionguard.xgwnje.cn/health` |
| API Key 变量 | `VISIONGUARD_API_KEY` / server `.env` 中的 `API_KEY`，不要在公开文档或提交中写明文 |

常用只读检查：

```bash
ssh xgwnje "systemctl status visionguard --no-pager -l | sed -n '1,30p'"
ssh xgwnje "systemctl is-active nginx visionguard"
ssh xgwnje "curl -ksS -o /dev/null -w '%{http_code}\n' https://visionguard.xgwnje.cn/health"
ssh xgwnje "ss -tlnp | grep -E ':(3000|8787|80|443|9443) ' || true"
```

## 密钥和敏感信息边界

| 项目 | 路径 / 说明 |
|---|---|
| SSH 私钥 | `~/.ssh/id_ed25519` |
| 证书私钥 | `/etc/nginx/private/`（各站点 SSL 私钥，勿外拷） |
| VisionGuard API Key | 使用环境变量 / server `.env`，不要写进仓库、PR、公开文档或聊天总结 |

涉及密钥、Reality 参数、代理节点、证书私钥时，只能读取必要状态，不要把明文复制进输出或提交。

## 核验参考命令

```powershell
ssh -F C:\Users\Administrator\.ssh\config xgwnje "hostname; uptime; free -h; df -h /"
ssh -F C:\Users\Administrator\.ssh\config xgwnje "systemctl is-active nginx visionguard"
ssh -F C:\Users\Administrator\.ssh\config xgwnje "curl -ksS -o /dev/null -w 'root %{http_code}\n' https://xgwnje.cn/; curl -ksS -o /dev/null -w 'vg %{http_code}\n' https://visionguard.xgwnje.cn/health; curl -ksS -o /dev/null -w 'status %{http_code}\n' https://status.xgwnje.cn/"
```
