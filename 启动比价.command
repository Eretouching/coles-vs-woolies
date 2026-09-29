#!/bin/bash
# 双击运行：启动比价工具并打开浏览器
cd "$(dirname "$0")"
(sleep 1 && open "http://localhost:8765") &
python3 server.py
