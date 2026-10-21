# LinknLink Remote - Home Assistant Add-ons Repository

Home Assistant 第三方加载项仓库，提供简单易用的远程访问解决方案。

## 关于

本仓库提供基于 LinknLink IoT 平台的 Home Assistant 远程访问服务。用 LinknLink 账号登录后，即可让您的 Home Assistant 实例从互联网上安全访问。

## 可用加载项

### 📡 LinknLink Remote

通过 LinknLink 平台实现 Home Assistant 远程访问的加载项。

**主要特性：**
- 远程访问免费：在加载项页面用 LinknLink 账号登录即可
- 可选 LinknLink 云访问，按主机授权（激活码 + 审核）
- 安全的加密隧道，自动重连
- 支持 aarch64、amd64（2.0.0 起不再支持 armv7）

[![安装加载项][addon-badge]][addon]

详细文档请查看：[frpc/README.md](frpc/README.md)

[addon-badge]: https://my.home-assistant.io/badges/supervisor_addon.svg
[addon]: https://my.home-assistant.io/redirect/supervisor_addon/?addon=a4a84f10_frpc

## 安装

### 方法 1: 一键添加

点击下方按钮一键添加本仓库：

[![添加仓库到 Home Assistant][add-repo-badge]][add-repo]

[add-repo-badge]: https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg
[add-repo]: https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Flinknlink%2Flinknlink-remote

### 方法 2: 手动添加

1. 打开 Home Assistant
2. 进入 **设置** → **加载项** → **加载项商店**
3. 点击右上角菜单（⋮）→ **仓库**
4. 添加仓库地址：`https://github.com/linknlink/linknlink-remote`
5. 点击 **添加**

### 安装加载项

添加仓库后，在加载项商店中找到所需的加载项，点击安装即可。

## 快速开始

安装 LinknLink Remote 加载项后：

1. 点击启动
2. 点击 **打开网页界面**（或使用侧边栏）
3. 使用 LinknLink 账号登录

详细文档请查看 [frpc/README.md](frpc/README.md)

## 常见问题

### 如何获取 LinknLink 账号？

注册 Linknlink APP开通账号。

### 加载项无法启动

自 2.0.0 起在加载项页面登录，配置项中已没有邮箱/密码。

1. 查看加载项 **日志** 页中的错误信息
2. 确认网络连接正常
3. 确认主机为 aarch64 或 amd64（2.0.0 起不支持 armv7）

### 更多帮助

- 📖 查看 [加载项文档](frpc/README.md)
- 🐛 [提交 Issue](https://github.com/linknlink/linknlink-remote/issues)
- 💬 联系 LinknLink 技术支持

## 支持

如有问题或建议，欢迎：

- 在 [GitHub Issues](https://github.com/linknlink/linknlink-remote/issues) 提交反馈
- 查看 [更新日志](frpc/CHANGELOG.md) 了解最新变化

---

**注意**：本仓库提供的加载项需要配合 LinknLink IoT 平台使用。
