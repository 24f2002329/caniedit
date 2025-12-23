from fastapi import APIRouter, UploadFile, File, HTTPException
from pypdf import PdfReader, PdfWriter
import uuid
import os

MAX_FILE_SIZE_MB = 10

router = APIRouter()

UPLOAD_DIR = "temp_uploads"
OUTPUT_DIR = "temp_outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@router.post("/merge")
async def merge_pdfs(files: list[UploadFile] = File(...)):
    writer = PdfWriter()
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024

    for file in files:
        file_size = getattr(file, "size", None)
        if file_size is not None and file_size > max_bytes:
            raise HTTPException(
                status_code=413,
                detail="File too large. Max 10MB allowed."
            )

        contents = await file.read()

        if file_size is None and len(contents) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail="File too large. Max 10MB allowed."
            )

        input_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.pdf")

        with open(input_path, "wb") as f:
            f.write(contents)

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
