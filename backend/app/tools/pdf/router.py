from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_optional_user
from app.db.session import get_db
from app.tools.pdf.service import delete_merged_pdf, merge_pdfs

router = APIRouter()


@router.post("/merge")
async def merge_pdfs_route(
	request: Request,
	files: list[UploadFile] = File(...),
	current_user=Depends(get_optional_user),
	db: Session = Depends(get_db),
):
	return await merge_pdfs(request, files, current_user, db)


@router.delete("/merge/{filename}")
def delete_merged_pdf_route(
	filename: str,
	current_user=Depends(get_optional_user),
	db: Session = Depends(get_db),
):
	return delete_merged_pdf(filename, current_user, db)


__all__ = ["router"]
