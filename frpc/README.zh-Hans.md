# Home Assistant Add-on: LinknLink Remote

通过 LinknLink 平台远程访问 Home Assistant，并可选开通 LinknLink 云访问。

![支持 aarch64 架构][aarch64-shield]
![支持 amd64 架构][amd64-shield]

## 关于

安装、启动，打开加载项页面，用 LinknLink 账号登录即可。加载项会把这台 Home Assistant 注册到 LinknLink，并保持加密的远程隧道在线，无需端口转发，也无需写 YAML。

## 功能

- 使用 LinknLink 账号登录后，**远程访问免费**
- **在加载项页面登录**（Home Assistant Ingress / 侧边栏），配置项中不再保存账号密码
- **可选云访问**，按主机授权：在 [LinknLink 商城](https://www.linknlink.com/products/linknlink-activation-code-for-linkhub) 购买激活码，在加载项页面提交订单号，等待审核
- 自动重连，页面中可直接查看状态

云访问目前仅支持海外（EU）LinknLink 账号。

## 安装

1. 进入 **设置** → **加载项** → **加载项商店**
2. 右上角菜单（⋮）→ **仓库**，添加 `https://github.com/linknlink/linknlink-remote`
3. 安装 **LinknLink Remote** 并点击 **启动**
4. 点击 **打开网页界面**（或开启 **在侧边栏中显示**）后登录

云访问、升级说明和故障排查请查看 **文档** 标签页。

## 支持的架构

- `aarch64` - ARM 64 位（如树莓派 4/5、Home Assistant Green/Yellow）
- `amd64` - x86_64（大多数 PC、NUC 和虚拟机）

自 2.0.0 起不再支持 armv7，armv7 设备将停留在 1.2.2。

## 从 1.x 升级

已移除邮箱/密码配置项。升级后请打开加载项页面登录一次。详见 [CHANGELOG.md](CHANGELOG.md)。

## 支持

- [GitHub Issues](https://github.com/linknlink/linknlink-remote/issues)
- LinknLink 客服

本加载项使用 [frp](https://github.com/fatedier/frp) 作为隧道客户端。

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
