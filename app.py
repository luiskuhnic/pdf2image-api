import os
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse

import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_c
from PIL import Image

app = FastAPI()

# Directorio donde se guardan las imágenes
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/tmp/output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def convert_from_bytes_pdfium(data: bytes, dpi: int = 200):
    """
    Convierte un PDF (en bytes) a una lista de objetos PIL.Image usando PDFium.
    """
    # Abrimos el documento desde bytes (sin named args)
    pdf = pdfium.PdfDocument(data)
    images = []
    scale = dpi / 72  # 1pt = 1/72in, así ajustamos DPI

    for page_index in range(len(pdf)):
        # Obtenemos y renderizamos la página
        page = pdf.get_page(page_index)
        bitmap = page.render(
            scale=scale,
            rotation=0,
            force_bitmap_format=pdfium_c.FPDFBitmap_BGRA,  # formato nativo PIL
            rev_byteorder=True,
        )
        # Convertimos a PIL y guardamos en memoria
        pil_img: Image.Image = bitmap.to_pil()
        images.append(pil_img)

        # Liberamos el bitmap y la página
        bitmap.close()
        page.close()

    pdf.close()
    return images


@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}


@app.post("/convert")
async def convert_pdf(file: UploadFile = File(...)):
    # Validación de extensión
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF")

    content = await file.read()

    # Intentamos convertir
    try:
        images = convert_from_bytes_pdfium(content, dpi=150)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al convertir PDF: {e}")

    # Creamos una sesión única para guardar resultados
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    urls = []
    for idx, img in enumerate(images, start=1):
        filename = f"page_{idx}.png"
        path = os.path.join(session_dir, filename)
        img.save(path, format="PNG")
        urls.append(f"/download/{session_id}/{filename}")
        img.close()  # libera también el PIL.Image

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
