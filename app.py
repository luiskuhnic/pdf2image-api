from fastapi import FastAPI, File, UploadFile, HTTPException
from pdf2image import convert_from_bytes
from fastapi.responses import FileResponse
import os
import uuid
import uvicorn

app = FastAPI()

# Directorio donde se guardan las imágenes
OUTPUT_DIR = "/data/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}

@app.post("/convert")
async def convert_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF")

    content = await file.read()
    images = convert_from_bytes(content)
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    filenames = []

    for i, img in enumerate(images):
        page_name = f"page_{i+1}.png"
        path = os.path.join(session_dir, page_name)
        img.save(path, "PNG")
        filenames.append(f"/download/{session_id}/{page_name}")

    return {"session_id": session_id, "images": filenames}

@app.get("/download/{session_id}/{filename}")
def download_image(session_id: str, filename: str):
    file_path = os.path.join(OUTPUT_DIR, session_id, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(file_path)

if __name__ == "__main__":
    # Leer el puerto que Render inyecta
    port = int(os.getenv("PORT", 8000))
    # Arrancar Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)

