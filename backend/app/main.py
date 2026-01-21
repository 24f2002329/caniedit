import threading

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import SessionLocal, init_db
from app.subscriptions.router import router as subscriptions_router
from app.tools.pdf.router import router as pdf_merge_router
from app.users.router import router as users_router
from app.users.service import cleanup_deleted_users_loop
from app.usage.tracker import cleanup_usage_rows_loop
from app.utils.storage import cleanup_old_files

app = FastAPI(
    title="CanIEdit API",
    description="Backend APIs for CanIEdit tools",
    version="0.1.0"
)


# ✅ CORS middleware (VERY IMPORTANT)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Root route
@app.get("/")
def root():
    return JSONResponse({
        "status": "ok",
        "message": "CanIEdit backend is running"
    })

# API routes
app.include_router(pdf_merge_router, prefix="/api/pdf")
app.include_router(subscriptions_router, prefix="/api")
app.include_router(users_router, prefix="/api")

# Serve merged files
app.mount(
    "/temp_outputs",
    StaticFiles(directory="temp_outputs"),
    name="temp_outputs"
)


@app.on_event("startup")
def start_cleanup_thread() -> None:
    init_db()
    threading.Thread(target=cleanup_old_files, daemon=True).start()
    threading.Thread(target=cleanup_deleted_users_loop, args=(SessionLocal,), daemon=True).start()
    threading.Thread(target=cleanup_usage_rows_loop, args=(SessionLocal,), daemon=True).start()
