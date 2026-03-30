# 1. 使用官方 Python 3.10 轻量级镜像作为基础
FROM python:3.10-slim

# 2. 安装系统依赖
RUN apt-get update && \
    apt-get install -y default-jre && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 3. 设置工作目录
WORKDIR /app

# 4. 复制依赖文件并安装 Python 包
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 复制应用代码到容器内
COPY . .

# 6. 赋予启动脚本可执行权限 (极其重要)
RUN chmod +x start.sh

# 7. 暴露 Gradio 默认端口
EXPOSE 7860

# 8. 修改启动命令：执行双进程启动脚本
CMD ["./start.sh"]