# VPS 核验快照与命令

## 最近核验（事实）

- 核验时间：2026-09-12（Asia/Shanghai）
- 核验方式：读取本机 SSH config（`~/.ssh/config`），并通过 SSH 在 VPS 上执行只读检查
- 当前默认 SSH 别名：`xgwnje`
- 兼容别名：`visionguard`、`server-infra-primary`、`server-infra-novixlink-lax`
- **重要变更**：稳定别名已切换至 NovixLink LAX 节点；旧目标仅以带 `-retired` 后缀的别名保留，不得用于常规操作

## SSH 连接（事实）

真实 IP / 端口 / 用户**不写进本文件**（本仓库为公开仓库）。以本机 `~/.ssh/config` 中的 `Host xgwnje` 条目为唯一事实源，用前现读：

```bash
ssh xgwnje                             # 登录默认 VPS
ssh xgwnje "uptime"                    # 远程执行只读命令
scp file.txt xgwnje:/var/www/          # 上传文件示例
```

在 Codex sandbox 中如果 `ssh xgwnje` 报 “Could not resolve hostname xgwnje”，通常是 sandbox 没读到用户 SSH config。可显式指定配置文件（路径以本机实际为准）。

## 服务器基本信息（2026-09-12 核验）

| 项目 | 当前值 |
|---|---|
| 系统 | Ubuntu 22.04.5 LTS (Jammy Jellyfish) |
| Kernel | `5.15.0-190-generic` |
| CPU | 1 vCPU |
| 内存 | 705 MiB；swap 1.0 GiB（已用约 77 MiB） |
| 根分区 | `/dev/vda1`，9.6G，已用 6.2G（65%） |
| 公网 IP / SSH | 见本机 `~/.ssh/config`（公开仓库不落明文） |

资源较此前 Debian 节点（1 vCPU / 961 MiB / 20G）进一步收缩，部署新服务前必须复核余量。

## Nginx 架构（事实）

配置文件在 `/etc/nginx/conf.d/`（不再是 sites-enabled）：

- `novix-web-9443.conf`：主页与 API 配置；主页 root 到静态目录，API 反代本机 Node 服务
- `novix-acme.conf`：`/.well-known/acme-challenge/` → `/var/www/acme`（证书签发）
- `novix-subscription-9443.conf`：`sub.xgwnje.cn` 订阅入口
- `novix-visionguard-9443.conf`：VisionGuard HTTPS / WebSocket 入口

## 当前服务分工（2026-09-12 核验）

| 域名 | 当前用途 | 后端 / 路径 | 核验结果 |
|---|---|---|---|
| `xgwnje.cn` / `www.xgwnje.cn` | 主页 | 静态 `/var/www/xgwnje-home` | `200` |
| `api.xgwnje.cn` | 主页 API | 反代本机 Node 服务（`127.0.0.1:8787` / `8790`） | 根路径 `404`，进程与监听端口在跑 |
| `visionguard.xgwnje.cn` | VisionGuard API / WebSocket | 反代 `127.0.0.1:3000` | `/health` 返回 `200` |
| `sub.xgwnje.cn` | 订阅 | 见 `novix-subscription-9443.conf` | 根路径 `404`；不据此判断订阅专用路径失效 |
| `m.xgwnje.cn` / `status.xgwnje.cn` / `mail.xgwnje.cn` | 旧机遗留域名 | 当前 Nginx 无对应站点配置 | HTTPS 连接失败，不得视为在役服务 |

注意（事实）：Docker 当前 inactive；旧文档中的 `webhome/current`、Uptime Kuma、status 页、移动版和 mail 预留站点均不得沿用。

## VisionGuard 部署（2026-09-12 核验）

| 项目 | 当前值 |
|---|---|
| 服务名 | `visionguard.service`（enabled，active） |
| systemd 文件 | `/etc/systemd/system/visionguard.service` |
| 工作目录 | `/opt/visionguard-server`（**不再是** `/opt/visionguard/VisionGuard_Server`） |
| 启动命令 | `/usr/bin/node dist/index.js` |
| Node 端口 | `127.0.0.1:3000` |
| 健康检查 | `curl -ksS https://visionguard.xgwnje.cn/health` |
| API Key 变量 | `VISIONGUARD_API_KEY` / server `.env` 中的 `API_KEY`（见「密钥零暴露」验收标准） |

常用只读检查：

```bash
ssh xgwnje "systemctl status visionguard --no-pager -l | sed -n '1,30p'"
ssh xgwnje "systemctl is-active nginx visionguard"
ssh xgwnje "curl -ksS -o /dev/null -w '%{http_code}\n' https://visionguard.xgwnje.cn/health"
ssh xgwnje "ss -tlnp | grep -E ':(3000|8787|80|443|9443) ' || true"
```

## 密钥和敏感信息位置（事实）

| 项目 | 路径 / 说明 |
|---|---|
| SSH 私钥 | 以 `ssh -G xgwnje` 解析出的 `identityfile` 为准，不在公开仓库固定文件名 |
| 证书私钥 | `/etc/nginx/private/`（各站点 SSL 私钥） |
| VisionGuard API Key | 环境变量 / server `.env` |

## 核验参考命令

```bash
ssh xgwnje "hostname; uptime; free -h; df -h /"
ssh xgwnje "systemctl is-active nginx visionguard"
ssh xgwnje "curl -ksS -o /dev/null -w 'root %{http_code}\n' https://xgwnje.cn/; curl -ksS -o /dev/null -w 'vg %{http_code}\n' https://visionguard.xgwnje.cn/health; curl -ksS -o /dev/null -w 'status %{http_code}\n' https://status.xgwnje.cn/"
```
