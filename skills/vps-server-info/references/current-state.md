# VPS 核验快照与命令

## 事实源与连接

- 核验时间：2026-11-09（Asia/Shanghai）；使用本机 SSH 配置及远程只读命令。
- 常规 SSH 别名：`server-infra-tokyo`，本轮连接成功。旧 `xgwnje` 入口连接关闭，不作为当前连接方案。
- 资源清单、生命周期与现场资料：私有仓库 `Wenje-Server/Server-infra` 的 `inventory/resources.json`、`state/current.json` 和 `CURRENT.md`。
- `CURRENT.md` 为 归属项目生成文件，本轮只读引用，未运行维护脚本或改写该项目。
- 真实连接参数以本机 SSH 配置为准；换机先按私有仓库恢复说明重新配置，公开技能不保存 IP、端口、用户、私钥路径或生产配置。

## 本轮实测

| 项目 | 观察 |
|---|---|
| 系统 / Kernel | Ubuntu 26.04 LTS / `7.0.0-30-generic` |
| CPU | 2 vCPU |
| 内存 | 总量 1930 MiB，可用约 1162 MiB |
| Swap | 总量 2047 MiB，已用约 784 MiB |
| 根分区 | 约 39G，已用 36G（96%），可用约 1.8G；部署前重新核验余量 |
| Nginx / VisionGuard | 均为 active |
| Docker | inactive，不据此推定应当启用 |
| 定时器 | `certbot.timer` active；`wenje-bandwidth.timer` inactive，未核验其他调度入口或邮件送达 |
| VisionGuard 健康检查 | `https://visionguard.xgwnje.cn/health` 返回 200；不代表设备、媒体与告警业务已验收 |

## VisionGuard 与配置定位

- 服务单元：`/etc/systemd/system/visionguard.service`。
- 当前工作目录：`/opt/visionguard-server`。
- Nginx `conf.d` 现有 `novix-visionguard-9443.conf`、`novix-subscription-9443.conf` 及订阅备份；文件存在不代表均生效，修改前按 归属项目核对加载链路。
- 公网入口与内部转发的期望关系见资源清单；本轮未转储 Nginx 配置、监听端口、环境变量或凭据。
- 旧主页、API、状态页和订阅入口不沿用 9 月快照推定在役；以 归属项目当前资源生命周期为准。

## 最小只读检查

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=yes server-infra-tokyo "uptime; free -m; df -h /"
ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=yes server-infra-tokyo "systemctl is-active nginx visionguard; systemctl show visionguard -p WorkingDirectory -p FragmentPath"
ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=yes server-infra-tokyo "curl -ksS -o /dev/null -w '%{http_code}\n' https://visionguard.xgwnje.cn/health"
```

以上 curl 只记录 HTTP 响应，`-k` 不验证证书信任；TLS、业务链路和资源余量按实际操作需要另行核验。服务器写入、服务操作及业务验收不包含在这份快照里。
