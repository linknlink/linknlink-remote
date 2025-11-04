# FRPC Add-on 快速开始指南

## 第一步：准备 GitHub 仓库

1. **创建 GitHub 仓库**
   - 在 GitHub 上创建一个新的公开仓库
   - 记录仓库地址：`https://github.com/Acmen0102/linknlink-remote`

2. **更新仓库信息**
   - 编辑 `repository.json`，更新 `url` 和 `maintainer`
   - 编辑 `addons/frpc/config.json`，更新 `url` 字段
   - 编辑 `addons/frpc/README.md`，替换所有示例中的仓库地址

3. **提交并推送代码**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: FRPC Add-on for Home Assistant"
   git remote add origin https://github.com/Acmen0102/linknlink-remote.git
   git branch -M main
   git push -u origin main
   ```

## 第二步：在 Home Assistant 中添加仓库

1. 打开 Home Assistant Web 界面
2. 进入 **Supervisor** → **加载项** → **加载项商店**
3. 点击右上角菜单（三个点图标 ☰）→ **仓库**
4. 输入您的仓库地址：`https://github.com/Acmen0102/linknlink-remote`
5. 点击 **添加**

## 第三步：安装 FRPC Add-on

1. 在加载项商店中，找到 **FRPC Client**
2. 点击进入详情页
3. 点击 **安装** 按钮
4. 等待安装完成（首次安装可能需要几分钟，因为需要下载 frp 并构建镜像）

## 第四步：配置

1. 点击 **配置** 标签页
2. 填写必需参数：
   ```json
   {
     "server_addr": "your-frp-server.com",
     "server_port": 7000
   }
   ```
3. 根据需要调整其他参数（可选）
4. 点击 **保存**

## 第五步：启动

1. 点击 **启动** 标签页
2. 点击 **启动** 按钮
3. 查看日志确认连接状态

## 常见配置示例

### 示例 1: 基本 TCP 连接（映射 SSH）

```json
{
  "server_addr": "frp.example.com",
  "server_port": 7000,
  "local_ip": "127.0.0.1",
  "local_port": 22,
  "remote_port": 6000,
  "proxy_name": "ssh",
  "protocol": "tcp"
}
```

### 示例 2: 映射 Home Assistant Web 界面

```json
{
  "server_addr": "frp.example.com",
  "server_port": 7000,
  "local_ip": "127.0.0.1",
  "local_port": 8123,
  "remote_port": 6000,
  "proxy_name": "homeassistant",
  "protocol": "tcp"
}
```

### 示例 3: 使用 Token 认证

```json
{
  "server_addr": "frp.example.com",
  "server_port": 7000,
  "token": "your-secret-token",
  "local_ip": "127.0.0.1",
  "local_port": 8123,
  "remote_port": 6000,
  "proxy_name": "homeassistant",
  "protocol": "tcp"
}
```

## 验证连接

启动后，查看日志应该能看到类似以下信息：

```
[2024-XX-XX XX:XX:XX] 正在启动 frpc...
[2024-XX-XX XX:XX:XX] 服务器地址: frp.example.com:7000
[2024-XX-XX XX:XX:XX] 本地地址: 127.0.0.1:8123
[2024-XX-XX XX:XX:XX] 远程端口: 6000
[2024-XX-XX XX:XX:XX] 代理名称: homeassistant
[2024-XX-XX XX:XX:XX] 协议类型: tcp
```

如果连接成功，frpc 会保持运行状态，您可以通过 `frp.example.com:6000` 访问您的服务。

## 故障排除

### 问题：仓库无法添加

- 确认仓库地址正确
- 确认仓库是公开的（Public）
- 确认 `repository.json` 文件在仓库根目录

### 问题：加载项无法显示

- 等待几分钟让 Home Assistant 同步
- 尝试刷新页面
- 检查仓库 URL 是否正确

### 问题：安装失败

- 检查网络连接
- 查看 Supervisor 日志
- 确认您的设备架构被支持

### 问题：连接失败

- 检查 `server_addr` 和 `server_port` 是否正确
- 确认 FRP 服务器正在运行
- 检查防火墙设置
- 如果使用 token，确认 token 是否正确

## 获取帮助

- 查看详细文档：`README.md`
- 提交 Issue：在 GitHub 仓库中提交问题
- FRP 官方文档：https://gofrp.org/docs/
