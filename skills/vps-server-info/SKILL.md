---
version: 1.4.0
name: vps-server-info
description: VPS 服务器连接信息（IP/端口/SSH/部署路径）。当项目需要 SSH 连接 VPS、部署 server、查询服务器配置时使用，目标是安全、准确地完成 VPS 相关操作。
---

# VPS 服务器信息

> 全局技能（事实档案 + 使用目标）。写法：目标模式——只描述想要的目标与验收标准，不规定具体做法；做法由模型按情境自决。
> 下文信息为 2026-07-24 核验快照，易变；本文档提供事实基线，不代替实时状态。

## 环境前提

此段仅声明事实，不规定 Agent 行为。

- **SSH 客户端**可用：`ssh` 命令在当前 shell 中可执行。Windows Git Bash 自带 OpenSSH 客户端，通常位于 `C:\Program Files\Git\usr\bin\ssh.exe`。
- **SSH 配置完整**：`~/.ssh/config` 中含 `Host xgwnje` 条目（主机名/IP/端口/用户均在该条目中，不落本文件）。SSH 私钥 `~/.ssh/id_ed25519` 存在且权限正确。
- **网络**：可达 VPS（Host xgwnje 的实际 IP 不在此文件——见 SSH config）。VPS SSH 端口（也在 config 中）未被防火墙拦截。
- **规格变化前提**：当前 VPS 为 2026-06-29 前后更换的新机器（1 vCPU / 961 MiB / 20G），低于旧机规格。2026-05-25 之前的旧文档（webhome 路径、Uptime Kuma、Docker）已全部作废。

## 使用目标

- **动手前状态可信**。验收：涉及发布、重启、证书、Nginx 改动的操作，执行前已通过实时核验确认当前状态（而非只依赖本文档快照）；本文档与实际输出不一致时以实时核验为准。
- **资源余量可见**。验收：部署新服务前，CPU / 内存 / 磁盘余量已被确认（参考「服务器基本信息」中的规格与占用）。
- **改动打在生效配置上**。验收：修改 `sub.xgwnje.cn` 订阅配置等有 .bak 备份并存的服务前，当前实际生效内容已被核对，改动未落在过期备份上。
- **清理不伤发布系统**。验收：清理 `/var/www/` 下 `xgwnje-home.backup-*` 等备份目录前，发布脚本对其的依赖已被确认。
- **密钥零暴露**。验收：输出、提交、公开文档、聊天总结中不存在 VisionGuard API Key、SSH 私钥、证书私钥、Reality 参数、代理节点等明文；涉及这些信息的操作只读取必要状态，未把明文复制进任何持久产物。

## 最近核验（事实）

- 核验时间：2026-07-24（Asia/Shanghai）
- 核验方式：读取本机 SSH config（`~/.ssh/config`），并通过 SSH 在 VPS 上执行只读检查
- 当前默认 SSH 别名：`xgwnje`
- 兼容旧别名：`visionguard`
- **重要变更**：2026-06-29 前后 VPS 更换过新机器，2026-05-25 之前的记录（webhome 路径、Uptime Kuma、Basic Auth 状态页、Docker）全部作废

## SSH 连接（事实）

真实 IP / 端口 / 用户**不写进本文件**（本仓库为公开仓库）。以本机 `~/.ssh/config` 中的 `Host xgwnje` 条目为唯一事实源，用前现读：

```bash
ssh xgwnje                             # 登录默认 VPS
ssh xgwnje "uptime"                    # 远程执行只读命令
scp file.txt xgwnje:/var/www/          # 上传文件示例
```

在 Codex sandbox 中如果 `ssh xgwnje` 报 “Could not resolve hostname xgwnje”，通常是 sandbox 没读到用户 SSH config。可显式指定配置文件（路径以本机实际为准）。

## 服务器基本信息（2026-07-24 核验）

| 项目 | 当前值 |
|---|---|
| 系统 | Debian GNU/Linux 12 (bookworm) |
| Kernel | `6.8.0-48-generic` |
| CPU | 1 vCPU |
| 内存 | 961 MiB，无 swap |
| 根分区 | `/dev/vda1`，20G，已用 11G（54%） |
| 公网 IP / SSH | 见本机 `~/.ssh/config`（公开仓库不落明文） |

规格比旧机（2 vCPU / 1.9G / 40G）缩水。

## Nginx 架构（事实）

配置文件在 `/etc/nginx/conf.d/`（不再是 sites-enabled）：

- `xgwnje-web-9443.conf`：主配置。外层 443 按域名分流到本机 `127.0.0.1:9443` 的各 per-host SSL server，再分别 root 到静态目录或反代后端
- `xgwnje-acme.conf`：`/.well-known/acme-challenge/` → `/var/www/acme`（证书签发）
- `xgwnje-mobile-subscription.conf`：`sub.xgwnje.cn` 订阅服务（有多个 .bak 备份）

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

注意（事实）：旧文档中的 `webhome/current` symlink 结构、Uptime Kuma（`127.0.0.1:3001`）、status 页 401 Basic Auth 均已不存在。`/var/www/` 下大量 `xgwnje-home.backup-*` 是发布系统产生的备份。

## VisionGuard 部署（2026-07-24 核验）

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
| SSH 私钥 | `~/.ssh/id_ed25519` |
| 证书私钥 | `/etc/nginx/private/`（各站点 SSL 私钥） |
| VisionGuard API Key | 环境变量 / server `.env` |

## 核验参考命令

```bash
ssh xgwnje "hostname; uptime; free -h; df -h /"
ssh xgwnje "systemctl is-active nginx visionguard"
ssh xgwnje "curl -ksS -o /dev/null -w 'root %{http_code}\n' https://xgwnje.cn/; curl -ksS -o /dev/null -w 'vg %{http_code}\n' https://visionguard.xgwnje.cn/health; curl -ksS -o /dev/null -w 'status %{http_code}\n' https://status.xgwnje.cn/"
```

## 环境自检

本 skill 被触发后，在向 VPS 发起任何写操作前，无声确认：

1. SSH config 含 `Host xgwnje` 条目：`ssh -G xgwnje` 能输出配置（不实际连接）
2. SSH 连接可用：`ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new xgwnje echo ok` 能返回 `ok`
3. 本文件快照年龄：对比核验时间（2026-07-24）与当前日期，向用户提示"VPS 快照已有 N 天未更新——请确认是否需先做一次实时核验"

自检通过 → 直接进入用户请求的操作。
任一前提不满足 → 见下方「失效模式」。

## 失效模式

| 前提失败 | 降级行为 |
|---|---|
| `Host xgwnje` 条目在 `~/.ssh/config` 中不存在 | 向 owner 报告："未找到 SSH Host xgwnje 配置。请在 `~/.ssh/config` 中添加该 Host 条目（IP/端口/用户），或告知当前 VPS 的 SSH 别名。"不尝试猜测或从本文件的其他位置构造连接参数。 |
| SSH 连接超时或认证失败 | 报告具体原因（超时=网络不可达或 VPS 已关机；认证失败=密钥过期或未注册）。**不重复尝试**（工具碰壁快速止损——同方式重试不超过两次）。提供诊断命令供 owner 自检。 |
| `~/.ssh/id_ed25519` 不存在 | 向 owner 确认密钥位置——可能用了不同的密钥类型或路径。不遍历文件系统搜索私钥文件。 |
| VPS 快照超过 30 天未更新 | 向 owner 强提示："VPS 信息快照已超过 30 天未核验。当前记录可能已过时。建议先运行核验命令刷新状态。"对本文件中的任何事实性断言，在报告中标注"基于 {核验日期} 快照，当前实际状态可能不同"。 |
| SSH 连接成功但远程命令返回异常（systemctl 报服务不存在、curl 返回意外状态码等） | 如实报告远程输出（脱敏处理）。不猜测原因——VPS 可能在 owner 不知道的情况下被改动。提供对比：本文档记录的状态 vs. 实测状态。 |
