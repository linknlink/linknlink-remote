# LinknLink Remote - Home Assistant Add-ons Repository

这是一个 Home Assistant 第三方加载项仓库，包含 FRPC Client 等加载项。

## 可用加载项

### FRPC Client

FRP 客户端（frpc）加载项，用于建立反向代理连接到 FRP 服务器。

详细文档请查看：[frpc/README.md](frpc/README.md)

## 安装方法

### 添加仓库到 Home Assistant

#### 方法 1: 通过 Web 界面

1. 打开 Home Assistant Web 界面
2. 进入 **Supervisor** → **加载项** → **加载项商店**
3. 点击右上角菜单（三个点图标）→ **仓库**
4. 输入您的仓库地址：

   ```text
   https://github.com/Acmen0102/linknlink-remote
   ```

5. 点击 **添加**

#### 方法 2: 通过 YAML 配置

在 Home Assistant 的 `configuration.yaml` 中添加：

```yaml
homeassistant:
  addon_repositories:
    - https://github.com/Acmen0102/linknlink-remote
```

然后重启 Home Assistant。

### 安装加载项

添加仓库后，在加载项商店中即可看到可用的加载项，点击进入详情页进行安装和配置。

## 快速开始

查看 [frpc/README.md](frpc/README.md) 了解详细的使用说明。

## 仓库结构

```text
.
├── repository.json          # 仓库配置文件
├── README.md               # 本文件
└── frpc/                   # FRPC Client Add-on
    ├── config.json         # Add-on 配置
    ├── Dockerfile          # Docker 镜像构建文件
    ├── run.sh              # 启动脚本
    └── README.md           # 详细文档
```

## 使用前准备

### 1. 更新仓库信息

在提交到 GitHub 之前，请更新以下文件中的仓库地址：

- `repository.json` - 更新 `url` 和 `maintainer` 字段
- `[addon-name]/config.json` - 更新 `url` 字段
- `[addon-name]/README.md` - 更新所有示例中的仓库地址

### 2. 添加图标（可选）

为 Add-on 添加一个图标可以提升用户体验：

1. 创建一个 128x128 像素的 PNG 图标
2. 保存为 `[addon-name]/icon.png`
3. 在 `config.json` 中添加图标引用（Home Assistant 会自动识别）

### 3. 发布到 GitHub

1. 初始化 Git 仓库（如果还没有）

   ```bash
   git init
   git add .
   git commit -m "Initial commit: Add Home Assistant Add-ons repository"
   ```

2. 创建 GitHub 仓库并推送

   ```bash
   git remote add origin https://github.com/Acmen0102/linknlink-remote.git
   git branch -M main
   git push -u origin main
   ```

3. 确保仓库是公开的（Public），或者确保 Home Assistant 有访问权限

## 验证安装

1. 在 Home Assistant 中添加仓库后
2. 进入 **加载项商店**
3. 应该能看到仓库中的所有加载项
4. 点击进入详情页，查看描述和配置选项
5. 按照各个 Add-on 的 README.md 中的说明进行安装和配置

## 故障排除

### 仓库无法添加

- 确认仓库地址正确
- 确认仓库是公开的
- 确认 `repository.json` 文件格式正确
- 检查网络连接

### 加载项无法显示

- 等待几分钟让 Home Assistant 同步仓库
- 尝试刷新页面
- 检查 `[addon-name]/config.json` 格式是否正确
- 查看 Home Assistant 日志中的错误信息

### 构建失败

- 检查 Dockerfile 语法
- 确认网络连接正常（需要下载依赖资源）
- 查看 Supervisor 日志

### Docker 镜像构建超时/失败

如果遇到类似 `Client.Timeout exceeded while awaiting headers` 的错误，通常是网络连接问题。

**快速解决方案：**

1. **国内用户**：配置 Docker 镜像加速器（强烈推荐）
   - 详细步骤请查看：[TROUBLESHOOTING.md](TROUBLESHOOTING.md)
   - 常用镜像加速器：中科大、网易、百度云、阿里云

2. **使用代理**：在 Home Assistant 系统上配置 Docker 代理
   - 详细步骤请查看：[TROUBLESHOOTING.md](TROUBLESHOOTING.md)

3. **检查网络**：确保可以访问 GitHub 和 Docker Hub
   - 测试命令：`curl -I https://registry-1.docker.io/v2/`

详细故障排除指南请查看：[TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

请根据您的需求添加相应的许可证文件。
