FROM python:3.12-slim

# curl：Coles 的防爬虫会拦 Python 自带的 HTTP 客户端，但放行 curl
# tzdata：每周三按悉尼时间检查特价
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates tzdata \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY *.py ./
COPY static ./static

# 数据库放在 /data。部署时必须在平台上把 /data 挂载成持久化存储（Zeabur：服务 → Volumes，
# Volume ID 填 data，Mount Directory 填 /data），否则每次重新部署数据都会清空。
# 这里刻意不写 VOLUME 指令，避免和平台自己挂载的存储卷冲突。
ENV HOST=0.0.0.0 \
    PORT=8080 \
    DATA_DIR=/data \
    WEEKLY_REFRESH=all \
    PYTHONUNBUFFERED=1
EXPOSE 8080

CMD ["python", "server.py"]
