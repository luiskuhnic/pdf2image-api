import os
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse

import pypdfium2 as pdfium
from PIL import Image

app = FastAPI()

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/tmp/output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}

@app.post("/convert")
async def convert_pdf(file: UploadFile = File(...)):
    # Validación de extensión
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF")

    content = await file.read()

    # Convertimos con PDFium usando la función de alto nivel
    try:
        scale = 150 / 72  # 150 DPI
        # Aquí pasas el contenido como primer argumento posicional:
        images = pdfium.render_topil(content, scale=scale, rotation=0, anti_alias=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al convertir PDF: {e}")

    # Guardamos cada página en disco
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    urls = []
    for i, img in enumerate(images, start=1):
        filename = f"page_{i}.png"
        path = os.path.join(session_dir, filename)
        img.save(path, "PNG")
        urls.append(f"/download/{session_id}/{filename}")
        img.close()

    return {"session_id": session_id, "images": urls}

@app.get("/download/{session_id}/{filename}")
def download_image(session_id: str, filename: str):
    file_path = os.path.join(OUTPUT_DIR, session_id, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(file_path)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
