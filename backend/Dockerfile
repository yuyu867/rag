# 后端镜像：Python 3.12 slim + FastAPI + LangGraph
FROM python:3.12-slim

WORKDIR /app

# 系统依赖：chromadb 的 onnxruntime 需要 libgomp
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 先装依赖再拷代码，充分利用构建缓存
# 国内服务器构建慢/失败时，可改用阿里云 PyPI 镜像（已默认启用，海外部署可去掉 -i 参数）
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

COPY . .

EXPOSE 8000

# 生产运行不带 --reload；数据目录通过 volume 挂载：
#   CHROMA_PERSIST_DIR=/data/chroma_db  CHECKPOINT_DB_PATH=/data/checkpoints.db
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
