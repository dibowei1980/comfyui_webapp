FROM python:3.11-slim AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y --no-install-recommends \
    git curl wget libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 aria2 && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

FROM base AS builder

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ && \
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 && \
    pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ && \
    pip install --no-cache-dir \
    GitPython PyGithub matrix-client==0.4.0 huggingface-hub>0.20 toml uv chardet typer rich typing-extensions \
    segment-anything scikit-image piexif opencv-python-headless dill matplotlib pandas pydub \
    watchdog>=3.0.0 gguf>=0.13.0 protobuf onnxruntime onnxruntime-gpu transparent-background \
    openpyxl soundfile gray2color simpleeval groundingdino-py transformers diffusers \
    hydra-core omegaconf iopath decord ftfy openai>=1.99.3 gallery-dl instaloader \
    googletrans-py google-genai>=1.51.0 PyYAML ultralytics==8.3.107 dynamicprompts \
    -i https://mirrors.aliyun.com/pypi/simple/ && \
    find /usr/local/lib/python3.11/site-packages -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true

FROM base AS runtime

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . /app/

RUN mkdir -p /app/models /app/input /app/output /app/temp /app/custom_nodes /app/user && \
    find /app -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true

EXPOSE 8188

ENV CUDA_VISIBLE_DEVICES=0 \
    COMFYUI_PATH=/app

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8188/system_stats || exit 1

CMD ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
