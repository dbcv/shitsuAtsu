FROM nvidia/cuda:13.1.2-cudnn-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv --break-system-packages

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY sam3 ./sam3

RUN uv sync --frozen

RUN uv pip install \
    torch torchvision \
    --extra-index-url https://download.pytorch.org/whl/cu132

COPY . .
