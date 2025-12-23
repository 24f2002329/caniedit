from fastapi import APIRouter, UploadFile, File, HTTPException
from pypdf import PdfReader, PdfWriter
import uuid
import os
import re
from typing import Final

MAX_FILE_SIZE_MB: Final = 10

router = APIRouter()

UPLOAD_DIR = "temp_uploads"
OUTPUT_DIR = "temp_outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@router.post("/merge")
async def merge_pdfs(files: list[UploadFile] = File(...)):
    writer = PdfWriter()
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024

    preserved_names: list[str] = []

    for index, file in enumerate(files, start=1):
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

        original_name = file.filename or f"document-{index}"
        stem, _ = os.path.splitext(original_name)
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", stem).strip("-").lower()
        if not slug:
            slug = f"file-{index}"
        preserved_names.append(slug)

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

    selected_names = preserved_names[:3]
    joined_names = "-".join(selected_names)
    if not joined_names:
        joined_names = "merged"
    if len(joined_names) > 60:
        joined_names = joined_names[:60].rstrip("-") or "merged"

    token = uuid.uuid4().hex[:6]
    output_name = f"caniedit-{joined_names}-{token}.pdf"
    output_path = os.path.join(OUTPUT_DIR, output_name)

    with open(output_path, "wb") as f:
        writer.write(f)

    return {
        "success": True,
        "file": output_name
    }


@router.delete("/merge/{filename}")
async def delete_merged_pdf(filename: str):
    if not re.fullmatch(r"[\w.-]+", filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        os.remove(file_path)
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Unable to delete file right now") from exc

    return {"success": True}
