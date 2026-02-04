# LinknLink Remote 项目结构说明

经过模块化重构，项目已从单一的 `web_config.py` 拆分为多个相互协作的 Python 模块。以下是重构后的项目目录结构及各模块职能说明：

## 1. 目录结构预览

```text
linknlink-remote/
├── .github/workflows/      # CI/CD 流程配置文件 (ci.yml)
├── common/
│   ├── rootfs/
│   │   ├── app/            # Python 核心服务代码
│   │   │   ├── templates/  # Flask HTML 模板 (index.html, login.html)
│   │   │   ├── main.py     # 程序入口
│   │   │   ├── config.py   # 全局配置与常量
│   │   │   ├── utils.py    # 通用工具函数
│   │   │   ├── device.py   # 设备 ID 与硬件信息管理
│   │   │   ├── cloud_service.py  # 云端交互 (登录、心跳上报)
│   │   │   ├── frpc_service.py   # Frpc 进程生命周期管理
│   │   │   ├── ieg_auth.py       # 本地 IEG 认证中间件
│   │   │   └── web_routes.py     # Web UI 路由与 API
│   │   └── docker-entrypoint.sh  # Docker 容器启动脚本
│   └── Dockerfile          # 容器镜像构建文件
├── scripts/                # 发布与构建脚本 (build-release.sh)
├── .vscode/                # IDE 调试配置 (launch.json)
├── VERSION                 # 版本管理文件
└── requirements.txt        # Python 依赖列表
```

## 2. 模块职能详细说明

### 核心框架
| 模块名 | 职能描述 |
| :--- | :--- |
| **`main.py`** | **程序大脑**。初始化 Flask 应用、启动后台心跳线程、检查 Frpc 配置文件并根据需要启动 Frpc 进程。同时也定义了 Flask 的启动参数（默认端口 8888）。 |
| **`config.py`** | **配置中枢**。统一管理所有文件路径（SERVICE_DIR, DATA_DIR）以及云端 API 地址。支持通过环境变量覆盖路径，方便本地开发。 |
| **`web_routes.py`** | **Web 交互**。定义所有的 HTTP 路由，包括首页展示、登录退出、API 配置保存、服务重启等逻辑。 |

### 业务逻辑模块
| 模块名 | 职能描述 |
| :--- | :--- |
| **`cloud_service.py`** | **云端交互**。负责用户登录云端获取 `companyid/userid`，并运行后台守护线程上报 `Heartbeat`。集成了原 `frpc-heartbeat.sh` 的逻辑。 |
| **`frpc_service.py`** | **运行控制**。负责 `frpc` 主进程及“远程协助”临时进程的 `Popen` 启动、`terminate` 停止及状态检查。 |
| **`device.py`** | **身份标识**。负责获取网卡 MAC 地址。如果获取失败，则生成 UUID，并将生成的 32 位 Device ID 持久化存储在 `/data/device_id.txt` 中。 |
| **`ieg_auth.py`** | **权限控制**。提供 `require_login` 装饰器，负责与本地 `ieg_auth` 服务校验 Token，确保 Web 管理界面的访问安全。 |
| **`utils.py`** | **工具套件**。包含通用的密码加密逻辑（SHA1+Salt）、JSON 内容比较（用于决定是否需要重启服务）以及端口生成逻辑。 |

## 3. 关键特性

*   **解耦**: 所有的 Web 逻辑与后台逻辑完全分离，进程管理不再依赖不可靠的 Shell 脚本。
*   **本地开发友好**: 开发者只需在本地运行 `python3 main.py`，并配合 `SERVICE_DIR` 环境变量，即可在不使用 Docker 的情况下进行完整的功能调试。
*   **资源占用低**: 后台任务使用原生 Python 线程，心跳上报频率可控。
*   **安全性**: 所有的敏感路径均可配置，关键操作（如修改配置）均经过认证过滤。
