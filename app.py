import os
import uuid

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse

import pypdfium2 as pdfium

app = FastAPI()

# Directorio de salida (puedes cambiarlo vía var. de entorno)
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/tmp/output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def convert_from_bytes_pdfium(data: bytes, dpi: int = 200):
    """
    Convierte un PDF (en bytes) a una lista de objetos PIL.Image usando PDFium.
    """
    # 1) Pasamos los bytes POSICIONALMENTE
    pdf = pdfium.PdfDocument(data)

    images = []
    scale = dpi / 72  # Convertimos dpi → escala PDFium

    for page_index in range(len(pdf)):
        # 2) Carga la página
        page = pdf.get_page(page_index)
        # 3) Renderiza a bitmap
        bitmap = page.render(
            scale=scale,
            rotation=0,
            anti_alias=True,
        )
        # 4) Pasa el bitmap a PIL
        pil_img = bitmap.to_pil()

        # 5) Liberamos recursos nativos
        bitmap.close()
        page.close()

        images.append(pil_img)

    pdf.close()
    return images

@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}

@app.post("/convert")
async def convert_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF")

    content = await file.read()

    try:
        images = convert_from_bytes_pdfium(content, dpi=150)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al convertir PDF: {e}")

    # Guardamos cada página
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    urls = []
    for i, img in enumerate(images, start=1):
        filename = f"page_{i}.png"
        path = os.path.join(session_dir, filename)
        img.save(path, format="PNG")
        img.close()
        urls.append(f"/download/{session_id}/{filename}")

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
    uvicorn.run("app:app", host="0.0.0.0", port=port, workers=1)
