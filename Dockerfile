FROM python:3.11-slim

# — Dependencias mínimas para PIL/pdfium —
RUN apt-get update \
 && apt-get install -y \
        libfontconfig1 \
        libgl1 \
        libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código
COPY . .

# Sólo expone un puerto (el de Render se inyecta en $PORT)
EXPOSE 8000

# Arranca en shell para que $PORT se expanda; usa un solo worker
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
