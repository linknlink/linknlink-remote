# Home Assistant Add-on: LinknLink Remote

通过 LinknLink 平台远程访问 Home Assistant，并可选开通 LinknLink 云访问。

## 运行要求

- **aarch64** 或 **amd64** 架构的 Home Assistant OS / Supervised 安装。
  自 2.0.0 起不再支持 armv7（32 位 ARM，例如较老的树莓派系统）。
- 一个 LinknLink 账号。如果还没有，请在 LinknLink App 中注册。

## 开始使用

1. 安装加载项并点击 **启动**。
2. 打开加载项页面：点击 **打开网页界面**，或开启 **在侧边栏中显示** 后使用侧边栏的 **LinknLink Remote**。
3. 使用 LinknLink 账号（邮箱/账号和密码）**登录**。

远程访问到这里就完成了：加载项会把这台 Home Assistant 注册到 LinknLink 平台并保持远程隧道在线。远程访问免费。

密码只会发送给 LinknLink 登录服务，不会保存在加载项配置中。

## 云访问（可选）

云访问让这台 Home Assistant 接入 LinknLink 云。授权按主机进行：加载项通过 Home Assistant OS / Supervisor 上报的主网卡 MAC 地址识别主机。

开通步骤：

1. 打开加载项页面并登录。
2. 点击 **Enable cloud access**。
3. 在 [LinknLink 商城](https://www.linknlink.com/products/linknlink-activation-code-for-linkhub) 购买激活码，下单时无需填写设备信息。
4. 复制 **订单号**，填入弹窗并点击 **Submit request**。
5. 等待审核。状态卡片会先显示 *Pending*，审核通过后显示 *Activating*，一般约 15 分钟内完成激活。
   如果申请被驳回，页面会显示驳回原因，修改订单号后可重新提交。

说明：

- 每个订单号只能绑定一台主机。
- 审核通过后，该主机的云访问永久有效。
- 授权绑定在主机主网卡上。更换该网卡或迁移到新硬件后，加载项会显示 **NIC changed**，请联系 LinknLink 客服迁移授权。
- 云访问目前仅支持海外（EU）LinknLink 服务的账号。

## 配置

登录在加载项页面完成，一般无需任何配置。

```yaml
log_level: info
```

- **log_level**：`trace`、`debug`、`info`（默认）、`notice`、`warning`、`error`、`fatal`。
- **guide_url** / **purchase_url**：页面中显示的帮助和商城链接，保持默认即可。

## 从 1.x 升级

- 已移除 `authentication` 邮箱/密码配置项。升级后请打开加载项页面登录一次。旧配置中残留的账号密码会在首次启动时自动清除。
- 原有设备 ID（`/data/device_id.txt`）会保留，设备在 LinknLink 平台上的身份不变。
- armv7 设备无法升级，将停留在 1.2.2。

## 故障排查

- **无法登录**：先在 LinknLink App 中确认账号和密码。提示“账号不存在”表示该账号尚未注册。
- **远程访问离线**：确认主机可以访问互联网，重启加载项并查看 **日志** 页。
- **云访问一直显示 Activating**：审核通过后最长约 15 分钟完成激活，可在页面中点击 **Refresh**。
- 日志中出现 **unable to resolve primary NIC MAC**：加载项无法从 Supervisor 读取主网卡，请确认主机有已连接的网卡后重启加载项。

其他问题请在 [GitHub](https://github.com/linknlink/linknlink-remote/issues) 提交 Issue 并附上加载项日志，或联系 LinknLink 客服。

## 致谢

- [frp](https://github.com/fatedier/frp) 提供隧道客户端。
