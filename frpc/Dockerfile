ARG BUILD_FROM=ghcr.io/hassio-addons/base:18.2.1
# hadolint ignore=DL3006
FROM ${BUILD_FROM}

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Set workdir
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



# Set environment variables
ENV LANG=C.UTF-8

# Copy root filesystem
COPY run.sh /run.sh
RUN chmod a+x /run.sh

# Build arguments
ARG BUILD_ARCH
ARG BUILD_DATE
ARG BUILD_DESCRIPTION
ARG BUILD_NAME="FRPC Client"
ARG BUILD_REF
ARG BUILD_REPOSITORY
ARG BUILD_VERSION

# Labels
LABEL \
    io.hass.name="${BUILD_NAME}" \
    io.hass.description="${BUILD_DESCRIPTION}" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version="${BUILD_VERSION}" \
    org.opencontainers.image.title="${BUILD_NAME}" \
    org.opencontainers.image.description="${BUILD_DESCRIPTION}" \
    org.opencontainers.image.vendor="LinknLink" \
    org.opencontainers.image.source="https://github.com/${BUILD_REPOSITORY}" \
    org.opencontainers.image.documentation="https://github.com/${BUILD_REPOSITORY}/blob/main/frpc/README.md" \
    org.opencontainers.image.created="${BUILD_DATE}" \
    org.opencontainers.image.revision="${BUILD_REF}" \
    org.opencontainers.image.version="${BUILD_VERSION}"

# Run script
CMD [ "/run.sh" ]
