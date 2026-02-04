ARG BUILD_FROM=alpine:latest
FROM ${BUILD_FROM}

ENV LANG C.UTF-8
ARG FRP_VERSION=0.67.0

# Install dependencies, Python, and download FRPC
# 使用默认 shell (sh) 安装 bash 和其他依赖
RUN \
    apk add --no-cache \
    bash \
    curl \
    jq \
    ca-certificates \
    util-linux \
    python3 \
    py3-pip \
    py3-cryptography \
    \
    # Install Python dependencies
    && pip3 install --break-system-packages flask requests

# Set shell to bash for complex logic
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN \
    # Download and install FRPC
    APK_ARCH=$(apk --print-arch) \
    && echo "Detected architecture: ${APK_ARCH}" \
    && case "${APK_ARCH}" in \
    x86_64) FRP_ARCH="amd64" ;; \
    aarch64) FRP_ARCH="arm64" ;; \
    armv7|armhf) FRP_ARCH="arm" ;; \
    *) echo "Error: Unsupported architecture: ${APK_ARCH}" && exit 1 ;; \
    esac \
    && echo "FRP architecture: ${FRP_ARCH}" \
    && FRP_URL="https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/frp_${FRP_VERSION}_linux_${FRP_ARCH}.tar.gz" \
    && echo "Downloading frp v${FRP_VERSION} from: ${FRP_URL}" \
    && curl -L -s --connect-timeout 30 --retry 3 "${FRP_URL}" -o /tmp/frp.tar.gz \
    && if [ ! -f /tmp/frp.tar.gz ] || [ ! -s /tmp/frp.tar.gz ]; then \
    echo "Failed to download frp" && exit 1; \
    fi \
    && tar -xzf /tmp/frp.tar.gz -C /tmp \
    && cp /tmp/frp_*/frpc /usr/local/bin/frpc \
    && chmod +x /usr/local/bin/frpc \
    && /usr/local/bin/frpc --version \
    && rm -rf /tmp/*

# Copy app files
COPY rootfs /

# Set workdir
WORKDIR /app

# Labels
LABEL     org.opencontainers.image.title="LinknLink Remote"     org.opencontainers.image.description="Enable remote access through the LinknLink platform"     org.opencontainers.image.vendor="LinknLink"     org.opencontainers.image.source="https://github.com/linknlink/linknlink-remote"     org.opencontainers.image.documentation="https://github.com/linknlink/linknlink-remote"

# Run script
ENTRYPOINT [ "python3", "/app/main.py" ]
