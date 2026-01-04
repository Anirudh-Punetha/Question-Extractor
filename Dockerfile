FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

WORKDIR /app
RUN apt-get update && apt-get install -y python3 python3-pip

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker \
    --workers 1 \
    --threads 1 \
    --timeout 300 \
    --bind 0.0.0.0:8000