---
version: 1.0.0
name: mini-vault
description: 中转站（get.xgwnje.cn / mini-vault）文件上传与下载核验。当需要把构建产物（APK/安装包/截图/日志等）传到中转站供用户自行下载到真机测试，或核验中转站可用性时使用。目标：上传前已获用户明确同意（问过才传，不擅自上传）；上传结果与下载链路均可核验（字节一致、目录可见、Range 可下）；交付给用户的链接与包信息完整。
---

# 中转站上传

写法：目标模式——下面的事实与验收标准是要达到的结果；具体命令为参考做法，可按情境调整。

## 站点事实（2026-08-01 实时核验）

- 站点：`https://get.xgwnje.cn/`，根路径即目录列表页，已传文件公开可见。
- 健康检查：`https://get.xgwnje.cn/health` 返回 `mini-vault ok`。
- 链路：公网 443 → nginx 按域名分流 → `127.0.0.1:9443`（get server 块，body 上限 2048m、关闭请求缓冲）→ `127.0.0.1:8787`（mini-vault 节点服务）→ dufs `127.0.0.1:5019`。
- dufs 启动参数：`--bind 127.0.0.1 --port 5019 --allow-upload --allow-delete --allow-search /var/lib/mini-vault`；上传/删除均无需鉴权（现状事实，公网可达——视为有意设计，不在本技能范围内改动）。
- 服务端排查（SSH 别名、nginx 架构、密钥纪律）以 vps-server-info skill 为准，需要时加载它。

## 验收标准

- **问过才传**：上传前已明确得到用户同意（对应全局规则「中转站真机验证兜底」）；未擅自上传。
- **命名可追溯**：文件名含项目名与版本号，形如 `<project>-v<x.y.z>.<ext>`（先例 `vigil-v1.9.0.apk`）；不带中文与空格。
- **上传可核验**：上传响应为 201，且已传字节数与本地文件大小一致。
- **下载可核验**：GET 目录列表出现该文件；Range 请求（`-r 0-99`）返回 206。
- **交付完整**：交给用户的不只是链接，还有包内容说明——版本号、签名类型（debug/release）、覆盖安装是否保留数据。

## 参考做法（非规定）

```bash
# 上传（PUT，响应 201 即成功）
curl -ksS -T <本地文件> "https://get.xgwnje.cn/<目标文件名>" \
  -w "HTTP=%{http_code} size=%{size_upload}\n" --max-time 300

# 核验：目录列表可见 + Range 可下（206）
curl -ksS https://get.xgwnje.cn/ | grep <目标文件名>
curl -ksS -o /dev/null -w "%{http_code}\n" -r 0-99 "https://get.xgwnje.cn/<目标文件名>"
```

## 失效模式

| 前提失败 | 降级行为 |
|---|---|
| 站点不可达或 `/health` 非 200 | 向 owner 报告实时状态，不盲目重试；服务端排查加载 vps-server-info skill（dufs 进程、nginx get server 块）。 |
| PUT 返回非 201 | 如实报告状态码与响应体；同方式重试不超 2 次，随后换等效路径：scp 到 VPS `dufs` 根目录 `/var/lib/mini-vault/`（先经 owner 确认）。 |
| 本地构建产物不存在 | 先构建再传；不把旧产物当新产物上传。 |
