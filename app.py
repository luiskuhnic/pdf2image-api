import os
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse

# Import básico de PIL y pdfium
import pypdfium2 as pdfium
from PIL import Image

app = FastAPI()

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/tmp/output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def convert_from_bytes_pdfium(data: bytes, dpi: int = 200):
    """
    Convierte un PDF a una lista de objetos PIL.Image usando PDFium.
    dpi: resolución deseada; ajusta para calidad/tamaño.
    """
    pdf = pdfium.PdfDocument(data=data)
    images = []
    scale = dpi / 72  # PDFium trabaja a 72 DPI base
    for page_index in range(len(pdf)):
        page = pdf.get_page(page_index)
        pil_img: Image.Image = page.render_topil(
            scale=scale,
            rotation=0,
            anti_alias=True,
        )
        images.append(pil_img)
        page.close()
    pdf.close()
    return images

@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}

@app.post("/convert")
async def convert_pdf(…):
    content = await file.read()
    pdf = pdfium.PdfDocument(data=content)
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    urls = []

    for i in range(len(pdf)):
        page = pdf.get_page(i)
        pil_img = page.render_topil(scale=150/72, anti_alias=True)
        filename = f"page_{i+1}.png"
        path = os.path.join(session_dir, filename)
        pil_img.save(path, "PNG")
        # liberamos todo inmediatamente
        pil_img.close()
        page.close()
        urls.append(f"/download/{session_id}/{filename}")

    pdf.close()
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
