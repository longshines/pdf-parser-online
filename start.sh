#!/bin/bash

echo "启动 OpenDataLoader Hybrid 后端服务 (端口 5002)..."
opendataloader-pdf-hybrid --port 5002 &

echo "等待后端服务初始化..."
sleep 5

echo "启动 Gradio 网页前端 (端口 7860)..."
python app.py