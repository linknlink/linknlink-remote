FROM alpine:latest

ENV LANG C.UTF-8
ARG FRP_VERSION=0.65.0

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install dependencies and download FRPC
RUN \
    apk add --no-cache \
        bash \
        curl \
        jq \
        util-linux \
    && apk add --no-cache --virtual .build-dependencies \
        wget \
    \
    && APK_ARCH=$(apk --print-arch) \
    && echo "Detected architecture: ${APK_ARCH}" \
    && FRP_ARCH=$( \
        case "${APK_ARCH}" in \
            x86_64) echo "amd64" ;; \
            aarch64) echo "arm64" ;; \
            armv7) echo "arm" ;; \
            *) echo "unsupported" ;; \
        esac \
    ) \
    && echo "FRP architecture: ${FRP_ARCH}" \
    && if [ "${FRP_ARCH}" = "unsupported" ]; then \
        echo "Error: Unsupported architecture: ${APK_ARCH}" && \
        exit 1; \
    fi \
    && FRP_URL="https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/frp_${FRP_VERSION}_linux_${FRP_ARCH}.tar.gz" \
    && echo "Downloading frp v${FRP_VERSION} for ${FRP_ARCH} from: ${FRP_URL}" \
    && wget -q --timeout=30 --tries=3 "${FRP_URL}" -O /tmp/frp.tar.gz \
    && if [ ! -f /tmp/frp.tar.gz ] || [ ! -s /tmp/frp.tar.gz ]; then \
        echo "Failed to download frp from ${FRP_URL}" && \
        echo "File exists: $([ -f /tmp/frp.tar.gz ] && echo 'yes' || echo 'no')" && \
        echo "File size: $([ -f /tmp/frp.tar.gz ] && ls -lh /tmp/frp.tar.gz | awk '{print $5}' || echo 'N/A')" && \
        exit 1; \
    fi \
    && tar -xzf /tmp/frp.tar.gz -C /tmp \
    && cp /tmp/frp_*/frpc /usr/local/bin/frpc \
    && chmod +x /usr/local/bin/frpc \
    && /usr/local/bin/frpc --version \
    && rm -f -r /tmp/* \
    && apk del --no-cache --purge \
        .build-dependencies

# Copy root filesystem
COPY rootfs /

# Ensure scripts are executable
RUN chmod +x /docker-entrypoint.sh /usr/local/bin/frpc-heartbeat.sh

# Labels
LABEL \
    org.opencontainers.image.title="LinknLink Remote" \
    org.opencontainers.image.description="Enable remote access through the LinknLink platform" \
    org.opencontainers.image.vendor="LinknLink" \
    org.opencontainers.image.source="https://github.com/linknlink/linknlink-remote" \
    org.opencontainers.image.documentation="https://github.com/linknlink/linknlink-remote"

# Run script
ENTRYPOINT [ "/docker-entrypoint.sh" ]

