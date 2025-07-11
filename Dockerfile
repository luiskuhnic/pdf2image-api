FROM python:3.11-slim
RUN apt-get update && apt-get install -y poppler-utils && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Cambia el puerto a una variable de entorno
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "${PORT}"]
