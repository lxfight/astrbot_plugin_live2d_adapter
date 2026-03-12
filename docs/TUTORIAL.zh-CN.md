# AstrBot Live2D Adapter 使用教程（含云服务器安全指引）

本文档重点解决两件事：

1. 如何快速装好并跑起来。
2. 云服务器场景下如何正确放通端口并保护服务器安全。

---

## 1. 安装（最简单方式）

如果你使用 AstrBot Dashboard：

1. 打开 **插件市场**。
2. 搜索并安装 `astrbot_plugin_live2d_adapter`。
3. 在平台配置中启用 `live2d` 适配器。

> 大多数用户只需要插件市场安装，不需要手动拷贝代码。

---

## 2. 首次配置（本机场景推荐）

建议先按本机安全模式配置：

```yaml
type: "live2d"
enable: true
id: "live2d_default"

ws_host: "127.0.0.1"
ws_port: 9090
ws_path: "/astrbot/live2d"
auth_token: ""
single_port_mode: true
public_origin: ""

resource_enabled: true
resource_path: "/resources"
resource_dir: "live2d_resources"
temp_dir: "live2d_temp"
resource_base_url: ""
resource_token: ""
```

### 关于 `auth_token`

- 现在为 **强制鉴权**。
- 如果留空，插件会自动生成高强度随机密钥，并写入：
  `data/plugin_data/astrbot-live2d-adapter/live2d_auth_token.txt`
- 请把该密钥填到桌面端「设置 -> 连接配置 -> 认证令牌」。

### 关于数据目录与本地文件

- 插件受管文件统一落在 `data/plugin_data/astrbot-live2d-adapter/` 下。
- `resource_dir` 默认是 `live2d_resources`，`temp_dir` 默认是 `live2d_temp`；它们都会解析到插件数据目录内。
- 这两个目录现在**不能**配置到插件数据目录外，越界的绝对路径会被拒绝。
- 桌面端传入的 `file:///` 图片、语音、文件、视频，会先复制到 `temp_dir` 再进入 AstrBot 流程。
- 适配器下发本地资源时，也会先复制到 `resource_dir`，再通过资源服务暴露；不会直接把原始 `file://` 路径返回给桌面端。

---

## 3. 云服务器部署（重点）

如果桌面端不在同一台机器，需要远程访问，请按下面做。

### 3.1 修改监听地址

将 `ws_host` 改为公网可监听地址（常见为 `0.0.0.0`），并保持 `single_port_mode: true`：

```yaml
ws_host: "0.0.0.0"
ws_port: 9090
single_port_mode: true
public_origin: "http://<你的公网IP或域名>:9090"  # 如使用反向代理，也可填写 https://example.com
```

`public_origin` 用于告诉桌面端应该从哪个公网入口访问 `/resources/{rid}`。如果你直接使用服务器 IP:端口 对外暴露，就填这个公网地址；如果走 Nginx/Caddy/宝塔反代，就填反代后的外部地址。

### 3.2 云厂商安全组放行（必须）

默认只需要放行一个 TCP 端口：

- `9090`（WebSocket + 资源接口）

强烈建议设置来源 IP 白名单，只允许你的桌面公网 IP。

### 3.3 服务器防火墙放行（必须）

#### Ubuntu / Debian（ufw）

```bash
# 仅允许固定来源 IP（推荐）
sudo ufw allow from <YOUR_DESKTOP_PUBLIC_IP> to any port 9090 proto tcp

# 查看规则
sudo ufw status numbered
```

#### CentOS / Rocky / AlmaLinux（firewalld）

```bash
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="<YOUR_DESKTOP_PUBLIC_IP>" port protocol="tcp" port="9090" accept'
sudo firewall-cmd --reload
sudo firewall-cmd --list-all
```

> 请不要直接对全网开放 9090，尤其不要在空口令/弱口令情况下运行。只有你主动关闭 `single_port_mode` 回退到旧双端口模式时，才需要额外放行 `resource_port`。

---

## 4. 如何保护自己的服务器（务必阅读）

### 最低安全基线

- 使用随机强密钥（长度至少 16，建议 32+）。
- 严格限制来源 IP（安全组 + 主机防火墙双层限制）。
- 只开放必要端口，不用的端口一律关闭。
- 定期轮换 `auth_token`，泄露后立即更换。
- 关注 AstrBot 与系统日志中的连接失败、异常请求。

### 进一步增强（推荐）

- 在具备条件时于反向代理层启用 HTTPS/WSS（TLS 证书）。
- 可将 WebSocket 与资源接口统一收敛到网关，仅暴露一个端口。
- 配置基础监控告警（连接暴增、异常流量、磁盘占用异常）。

---

## 5. 桌面端如何连接

在 `astrbot-live2d-desktop` 里：

1. 打开「设置 -> 连接」。
2. 服务器地址填：
   - `ws://<SERVER_IP>:9090/astrbot/live2d`
   - 或你的 `wss://` 代理地址
3. 填写与服务端一致的认证令牌。
4. 一般不需要填写「高级资源设置」；只有老版本适配器或特殊端口映射场景才需要额外覆盖资源地址。
5. 点击连接。

---

## 6. 常用功能与命令

### 管理命令（在 AstrBot 使用）

- `/live2d status`：看在线状态、连接数、资源使用。
- `/live2d info`：看当前客户端详情（模型、动作组等）。
- `/live2d list`：查看连接客户端列表。
- `/live2d resources`：看资源占用。
- `/live2d cleanup`：手动清理（管理员）。
- `/live2d config`：查看当前配置（管理员）。

兼容旧写法：`/live2d.status`、`/live2d.info` 等点号命令仍可使用。

完整说明见：`COMMANDS.md`

### 常见功能

- 文本、图片、语音输入到 AstrBot。
- 回复转换为 Live2D 表演序列（文字、动作、表情、语音）。
- 资源服务自动处理大文件 URL/引用。

---

## 7. 快速排障

### 桌面端提示认证失败

- 检查桌面端 token 与服务端 `auth_token` 是否完全一致。
- 检查是否复制了多余空格/换行。

### 连接不上云服务器

- 检查安全组是否放行 9090。
- 检查 Linux 防火墙是否放行相同端口。
- 如通过反向代理或公网域名访问，检查 `public_origin` 是否填写为桌面端真实可访问的外部地址。
- 检查 `ws_path` 是否为 `/astrbot/live2d`。

### 图片/语音资源加载失败

- 检查桌面端是否能访问 `http(s)://<服务地址>/resources/{rid}`。
- 检查 `resource_enabled`、`public_origin` 与 `resource_base_url` 配置。
- 若仍使用旧双端口模式，再检查 `resource_port` 与桌面端高级资源设置。

---

## 8. 推荐阅读

- 协议文档：`API.md`
- 管理命令：`COMMANDS.md`
- 桌面端教程：请查看 `astrbot-live2d-desktop/docs/USAGE_TUTORIAL.zh-CN.md`
