import os
import re
import uuid
from typing import Final

from fastapi import HTTPException, Request, UploadFile, status
from pypdf import PdfReader, PdfWriter
from sqlalchemy.orm import Session

from app.db.models.file import FileRecord
from app.usage.tracker import increment_usage

MAX_FILE_SIZE_MB: Final = 10
UPLOAD_DIR = "temp_uploads"
OUTPUT_DIR = "temp_outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def merge_pdfs(
	request: Request,
	files: list[UploadFile],
	current_user,
	db: Session,
) -> dict:
	# Enforce daily usage before processing.
	increment_usage(db, request, current_user, tool="pdf_merge")

	writer = PdfWriter()
	max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024

	preserved_names: list[str] = []

	for index, file in enumerate(files, start=1):
		file_size = getattr(file, "size", None)
		if file_size is not None and file_size > max_bytes:
			raise HTTPException(
				status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
				detail="File too large. Max 10MB allowed.",
			)

		contents = await file.read()

		if file_size is None and len(contents) > max_bytes:
			raise HTTPException(
				status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
				detail="File too large. Max 10MB allowed.",
			)

		original_name = file.filename or f"document-{index}"
		stem, _ = os.path.splitext(original_name)
		slug = re.sub(r"[^a-zA-Z0-9]+", "-", stem).strip("-").lower()
		if not slug:
			slug = f"file-{index}"
		preserved_names.append(slug)

		input_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.pdf")

		with open(input_path, "wb") as handle:
			handle.write(contents)

		reader = PdfReader(input_path)

		# 🔐 Handle encrypted PDFs
		if reader.is_encrypted:
			try:
				decrypted = reader.decrypt("")  # try empty password
			except Exception:
				decrypted = 0

			if not decrypted:
				raise HTTPException(
					status_code=status.HTTP_400_BAD_REQUEST,
					detail="One of the PDFs is password protected. Please unlock it first and try again.",
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

	with open(output_path, "wb") as handle:
		writer.write(handle)

	if current_user:
		file_record = FileRecord(
			user_id=current_user.id,
			tool="pdf_merge",
			filename=output_name,
			storage_path=output_path,
		)
		db.add(file_record)
		db.commit()

	return {
		"success": True,
		"file": output_name,
	}


def delete_merged_pdf(filename: str, current_user, db: Session) -> dict:
	if not re.fullmatch(r"[\w.-]+", filename):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")

	file_record = db.query(FileRecord).filter(FileRecord.filename == filename).first()
	if file_record:
		if not current_user:
			raise HTTPException(
				status_code=status.HTTP_401_UNAUTHORIZED,
				detail="Missing authorization token",
				headers={"WWW-Authenticate": "Bearer"},
			)
		if file_record.user_id != current_user.id:
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this file")

	file_path = os.path.join(OUTPUT_DIR, filename)
	if not os.path.isfile(file_path):
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

	try:
		os.remove(file_path)
	except OSError as exc:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to delete file right now") from exc

	if file_record:
		db.delete(file_record)
		db.commit()

	return {"success": True}
