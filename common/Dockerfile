# syntax=docker/dockerfile:1
#
# LinknLink Remote add-on image.
#
# The add-on ships prebuilt binaries only. They are published as assets of the
# GitHub Release v<version>:
#   linknlink-remote-frpc-<version>-<arch>.tar.gz
# containing bin/, frp/frpc, rootfs/ and configs/.
#
# The download/verify/extract step runs in a stage on the *build* platform, so
# the final (target-arch) stage needs no RUN and no qemu emulation.
ARG BUILD_FROM=ghcr.io/hassio-addons/debian-base:7.8.3

FROM --platform=$BUILDPLATFORM ${BUILD_FROM} AS artifact
ARG BUILD_ARCH
ARG BUILD_VERSION
ARG ARTIFACT_SHA256_AARCH64
ARG ARTIFACT_SHA256_AMD64
# Override for local testing, e.g. http://127.0.0.1:8000
ARG ARTIFACT_BASE_URL=https://github.com/linknlink/linknlink-remote/releases/download
ARG ARTIFACT_TAG=v${BUILD_VERSION}
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN set -eux; \
    case "${BUILD_ARCH}" in \
      aarch64) sha="${ARTIFACT_SHA256_AARCH64}" ;; \
      amd64)   sha="${ARTIFACT_SHA256_AMD64}" ;; \
      *) echo "unsupported BUILD_ARCH=${BUILD_ARCH}" >&2; exit 1 ;; \
    esac; \
    name="linknlink-remote-frpc-${BUILD_VERSION}-${BUILD_ARCH}.tar.gz"; \
    curl -fsSL --retry 3 -o "/tmp/${name}" "${ARTIFACT_BASE_URL}/${ARTIFACT_TAG}/${name}"; \
    if [ -n "${sha}" ]; then \
      echo "${sha}  /tmp/${name}" | sha256sum -c -; \
    else \
      echo "WARNING: no sha256 pinned for ${BUILD_ARCH}" >&2; \
    fi; \
    mkdir -p /out; \
    tar -xzf "/tmp/${name}" -C /out; \
    test "$(cat /out/VERSION)" = "${BUILD_VERSION}"; \
    test -x /out/bin/remote-manager -a -x /out/frp/frpc

FROM ${BUILD_FROM}

ENV LANG=C.UTF-8

COPY --from=artifact --chmod=0755 \
    /out/bin/iegcloudaccess /out/bin/linknlinkedge /out/bin/ha2devicehub /out/bin/remote-manager \
    /usr/local/bin/
COPY --from=artifact --chmod=0755 /out/frp/frpc /opt/frpc-assets/frpc
COPY --from=artifact --chmod=0755 /out/frp/frpc /usr/local/bin/frpc
COPY --from=artifact /out/rootfs/ /
COPY --from=artifact /out/configs/ /etc/linknlink/

ENV IEG_CONFIG=/etc/linknlink/iegcloudaccess.toml \
    LINKNLINKEDGE_CONFIG=/etc/linknlink/linknlinkedge.yaml \
    HA2DEVICEHUB_CONFIG=/etc/linknlink/ha2devicehub.toml \
    HA_AUTH_MODE=supervisor \
    ACTIVATION_TYPE=halicense

ARG BUILD_ARCH
ARG BUILD_DATE
ARG BUILD_DESCRIPTION
ARG BUILD_NAME="LinknLink Remote"
ARG BUILD_REF
ARG BUILD_REPOSITORY=linknlink/linknlink-remote
ARG BUILD_VERSION

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
    org.opencontainers.image.documentation="https://github.com/${BUILD_REPOSITORY}/blob/main/frpc/DOCS.md" \
    org.opencontainers.image.created="${BUILD_DATE}" \
    org.opencontainers.image.revision="${BUILD_REF}" \
    org.opencontainers.image.version="${BUILD_VERSION}"
