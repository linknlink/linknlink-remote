# 工作流分析：参考项目 vs 我们的项目

## 参考项目（addon-ssh, addon-wireguard）

### 工作流文件

1. **ci.yaml**
   ```yaml
   jobs:
     workflows:
       uses: hassio-addons/workflows/.github/workflows/addon-ci.yaml@main
   ```
   - **功能**：CI 检查
   - **执行内容**：
     - 验证 `config.yaml` 格式
     - 检查 Dockerfile 语法
     - 验证 build.yaml 配置
     - 代码质量检查
   - **触发**：push、pull_request

2. **deploy.yaml**
   ```yaml
   jobs:
     workflows:
       uses: hassio-addons/workflows/.github/workflows/addon-deploy.yaml@main
   ```
   - **功能**：构建和推送 Docker 镜像
   - **执行内容**：
     - 根据 build.yaml 构建多架构镜像
     - 推送到 GHCR（GitHub Container Registry）
     - 创建版本标签
   - **触发**：release、CI 通过后
   - **前提**：config.yaml 中没有 `image` 字段（本地构建）

3. **其他工作流**
   - `labels.yaml` - 同步标签（定时任务）
   - `release-drafter.yaml` - 自动生成发布说明
   - `stale.yaml` - 标记过期的 issue/PR
   - `lock.yaml` - 锁定已关闭的 issue/PR
   - `pr-labels.yaml` - PR 标签管理

### 镜像构建方式

- **本地构建**：config.yaml 中没有 `image` 字段
- **构建时机**：通过 deploy.yaml 在 CI 通过后构建
- **镜像仓库**：GHCR（GitHub Container Registry）
- **架构支持**：aarch64, amd64, armv7

## 我们的项目（linknlink-remote）

### 工作流文件

1. **ci.yaml**
   ```yaml
   jobs:
     addon:
       uses: hassio-addons/workflows/.github/workflows/addon-ci.yaml@main
       with:
         addons: frpc
   ```
   - **功能**：CI 检查（与参考项目相同）
   - **执行内容**：验证配置、检查代码等

2. **build-and-push.yml**
   ```yaml
   # 自定义工作流，不使用官方可重用工作流
   ```
   - **功能**：构建和推送预构建镜像
   - **执行内容**：
     - 根据矩阵构建多架构镜像（aarch64, amd64, armv7）
     - 推送到 GHCR
     - 创建版本标签和 latest 标签
   - **触发**：push 到 main、release、手动触发
   - **前提**：config.yaml 中有 `image` 字段（预构建镜像）

3. **其他工作流**（与参考项目相同）
   - `labels.yaml` - 同步标签
   - `release-drafter.yaml` - 自动生成发布说明
   - `stale.yaml` - 标记过期的 issue/PR
   - `lock.yaml` - 锁定已关闭的 issue/PR
   - `pr-labels.yaml` - PR 标签管理

### 镜像构建方式

- **预构建镜像**：config.yaml 中有 `image: ghcr.io/acmen0102/linknlink-remote-frpc:{arch}` 字段
- **构建时机**：通过 build-and-push.yml 在代码推送时构建
- **镜像仓库**：GHCR（GitHub Container Registry）
- **架构支持**：aarch64, amd64, armv7

## 关键区别

| 项目 | 构建方式 | 工作流 | 镜像字段 |
|------|---------|--------|----------|
| **参考项目** | 本地构建 | deploy.yaml（官方可重用） | 无 `image` 字段 |
| **我们的项目** | 预构建镜像 | build-and-push.yml（自定义） | 有 `image` 字段 |

## 为什么我们使用自定义工作流？

1. **预构建镜像需求**：
   - Home Assistant 安装时直接拉取预构建镜像
   - 不需要在本地构建，安装更快

2. **官方工作流限制**：
   - `addon-deploy.yaml` 期望本地构建（没有 `image` 字段）
   - 我们的项目使用预构建镜像（有 `image` 字段）
   - 所以需要自定义工作流来构建和推送镜像

3. **灵活性**：
   - 自定义工作流可以控制构建流程
   - 可以添加自定义的标签策略
   - 可以优化构建缓存

## 总结

参考项目的工作流：
- ✅ 使用官方可重用工作流进行 CI 和部署
- ✅ deploy.yaml 构建和推送镜像（本地构建场景）
- ✅ 没有预构建镜像的操作（因为使用本地构建）

我们的项目：
- ✅ 使用官方可重用工作流进行 CI
- ✅ 使用自定义工作流构建和推送预构建镜像
- ✅ 预构建镜像由 build-and-push.yml 负责

两种方式都是正确的，选择取决于项目需求：
- **本地构建**：安装时构建，适合开发环境
- **预构建镜像**：安装时直接拉取，适合生产环境（更快）

