# syntax=docker/dockerfile:1

# Unit tests. The add-on itself still runs inside Blender.
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS test

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock README.md LICENSE.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --all-groups

COPY tests ./tests
COPY pytest.ini addon.py __init__.py main.py ./

CMD ["uv", "run", "pytest"]

# Headless Blender 4.5 LTS. Registers and unregisters the add-on, then exits.
FROM debian:bookworm-slim AS blender

ARG BLENDER_VERSION=4.5.14
ARG BLENDER_SHA256=9ba871ff2ecd36526b77432745980b7e6664ecd0c7ca11c48849073dcfe06da3

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        xz-utils \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libx11-6 \
        libxext6 \
        libxfixes3 \
        libxi6 \
        libxrender1 \
        libxxf86vm1 \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL \
        -o /tmp/blender.tar.xz \
        "https://download.blender.org/release/Blender4.5/blender-${BLENDER_VERSION}-linux-x64.tar.xz" \
    && echo "${BLENDER_SHA256}  /tmp/blender.tar.xz" | sha256sum -c - \
    && mkdir -p /opt/blender \
    && tar -xJf /tmp/blender.tar.xz -C /opt/blender --strip-components=1 \
    && rm /tmp/blender.tar.xz \
    && ln -s /opt/blender/blender /usr/local/bin/blender

WORKDIR /opt/addon
COPY addon.py __init__.py ./
COPY src ./src
COPY scripts/blender_smoke.py ./scripts/blender_smoke.py

CMD ["blender", "--background", "--python", "/opt/addon/scripts/blender_smoke.py"]
