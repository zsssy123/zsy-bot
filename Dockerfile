# 使用 Python 3.11 的官方瘦版镜像
FROM python:3.11-slim

# 安装 tesseract 和中文语言包
RUN apt-get update && \
    apt-get install -y tesseract-ocr tesseract-ocr-chi-sim && \
    rm -rf /var/lib/apt/lists/*

# 安装 Python 项目依赖
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝你的代码（假设代码都在当前目录）
COPY . /app
WORKDIR /app

# 启动服务（你也可以写成 gunicorn 或其他）
CMD ["python", "bot.py"]
