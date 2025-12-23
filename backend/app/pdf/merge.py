from fastapi import APIRouter, UploadFile, File, HTTPException
from pypdf import PdfReader, PdfWriter
import uuid
import os

router = APIRouter()

UPLOAD_DIR = "temp_uploads"
OUTPUT_DIR = "temp_outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@router.post("/merge")
async def merge_pdfs(files: list[UploadFile] = File(...)):
    writer = PdfWriter()

    for file in files:
        input_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.pdf")

        with open(input_path, "wb") as f:
            f.write(await file.read())

        reader = PdfReader(input_path)

        # 🔐 Handle encrypted PDFs
        if reader.is_encrypted:
            try:
                reader.decrypt("")  # try empty password
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="One of the PDFs is password protected and cannot be merged."
                )

        for page in reader.pages:
            writer.add_page(page)

    output_name = f"{uuid.uuid4()}_merged.pdf"
    output_path = os.path.join(OUTPUT_DIR, output_name)

    with open(output_path, "wb") as f:
        writer.write(f)

    return {
        "success": True,
        "file": output_name
    }
