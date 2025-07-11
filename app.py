from fastapi import FastAPI, File, UploadFile, HTTPException
from pdf2image import convert_from_bytes
import os
import uuid
from fastapi.responses import FileResponse

app = FastAPI()

OUTPUT_DIR = "/data/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}

@app.post("/convert")
async def convert_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF")

    content = await file.read()
    images = convert_from_bytes(content)
    session_id = str(uuid.uuid4())
    session_dir = f"{OUTPUT_DIR}/{session_id}"
    os.makedirs(session_dir, exist_ok=True)
    filenames = []

    for i, img in enumerate(images):
        path = f"{session_dir}/page_{i+1}.png"
        img.save(path, "PNG")
        filenames.append(f"/download/{session_id}/page_{i+1}.png")

    return {"session_id": session_id, "images": filenames}

@app.get("/download/{session_id}/{filename}")
def download_image(session_id: str, filename: str):
    file_path = f"{OUTPUT_DIR}/{session_id}/{filename}"
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(file_path)

if __name__ == "__main__":
    import uvicorn
    # Leer el puerto que Render inyecta, o usar 8000 por defecto
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
