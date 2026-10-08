FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# ModelScope 创空间只对外暴露 7860 端口，应用必须监听 0.0.0.0:7860
ENV PORT=7860
EXPOSE 7860

ENTRYPOINT ["python", "-u", "app.py"]
