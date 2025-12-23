import threading

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.pdf.merge import router as pdf_merge_router
from app.utils.cleanup import cleanup_old_files

app = FastAPI(
    title="CanIEdit API",
    description="Backend APIs for CanIEdit tools",
    version="0.1.0"
)


# ✅ CORS middleware (VERY IMPORTANT)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later we’ll restrict this
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

# Serve merged files
app.mount(
    "/temp_outputs",
    StaticFiles(directory="temp_outputs"),
    name="temp_outputs"
)


@app.on_event("startup")
def start_cleanup_thread() -> None:
    threading.Thread(target=cleanup_old_files, daemon=True).start()
