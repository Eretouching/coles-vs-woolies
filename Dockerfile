FROM python:3.12-slim

# curl：Coles 的防爬虫会拦 Python 自带的 HTTP 客户端，但放行 curl
# tzdata：每周三按悉尼时间检查特价
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates tzdata \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY *.py ./
COPY static ./static

# 数据库放在 /data，部署时把这个目录挂载成持久化存储（Volume）
ENV HOST=0.0.0.0 \
    PORT=8080 \
    DATA_DIR=/data \
    PYTHONUNBUFFERED=1
VOLUME /data
EXPOSE 8080

CMD ["python", "server.py"]
