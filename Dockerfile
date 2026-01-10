# syntax=docker/dockerfile:1.6
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps:
# - git: to clone repos
# - graphviz: optional, for --render PNGs (dot)
# - ca-certificates: TLS
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      git \
      graphviz \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install API deps first for better Docker layer caching
COPY api/requirements.txt /app/api/requirements.txt
RUN pip install -r /app/api/requirements.txt

# Copy the rest of the repo and install dpylens
COPY . /app
RUN pip install -e .

EXPOSE 8787

# Persist run outputs
VOLUME ["/app/.dpylens-server"]

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8787"]