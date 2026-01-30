# 强制重新构建（解决 Zeabur 缓存问题）
ARG CACHEBUST=20260131-11

FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

# 给启动脚本执行权限
RUN chmod +x /app/start.sh

# 使用启动脚本（有完整的日志捕获）
CMD ["/app/start.sh"]

# 备用启动命令：如果 Zeabur 不使用 CMD，可以设置这个
# 在 Zeabur 的 Start Command 中填入: python /app/simple_test.py
