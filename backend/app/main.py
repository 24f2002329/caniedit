from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.pdf.merge import router as pdf_merge_router

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
