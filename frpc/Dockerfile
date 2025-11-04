ARG BUILD_FROM=ghcr.io/hassio-addons/base:14.2.0
FROM ${BUILD_FROM}

# 设置工作目录
WORKDIR /root

# 安装必要的依赖
RUN apk add --no-cache \
    curl \
    wget \
    ca-certificates

# 定义 frp 版本和架构
ARG FRP_VERSION=0.52.3
ARG TARGETARCH

# 根据架构设置下载URL
# 注意: Home Assistant 使用 TARGETARCH，但 frp 发布包使用不同的架构名称
RUN case ${TARGETARCH} in \
    "amd64") FRP_ARCH="amd64" ;; \
    "arm64"|"aarch64") FRP_ARCH="arm64" ;; \
    "arm") FRP_ARCH="arm" ;; \
    "386"|"i386") FRP_ARCH="386" ;; \
    *) echo "Unsupported architecture: ${TARGETARCH}" && exit 1 ;; \
    esac && \
    FRP_URL="https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/frp_${FRP_VERSION}_linux_${FRP_ARCH}.tar.gz" && \
    echo "Downloading frp v${FRP_VERSION} for ${FRP_ARCH} from: ${FRP_URL}" && \
    wget -q "${FRP_URL}" -O /tmp/frp.tar.gz && \
    if [ ! -f /tmp/frp.tar.gz ] || [ ! -s /tmp/frp.tar.gz ]; then \
        echo "Failed to download frp" && exit 1; \
    fi && \
    tar -xzf /tmp/frp.tar.gz -C /tmp && \
    cp /tmp/frp_*/frpc /usr/local/bin/frpc && \
    chmod +x /usr/local/bin/frpc && \
    /usr/local/bin/frpc version && \
    rm -rf /tmp/frp* && \
    apk del wget curl || true

# 复制运行脚本
COPY run.sh /run.sh
RUN chmod a+x /run.sh

# 设置环境变量
ENV LANG=C.UTF-8

# 运行脚本
CMD [ "/run.sh" ]
