import os
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .core.logging import logger
from .core.exceptions import InsightXException
from .api.v1.router import router as api_v1_router
from .database.session import Base, engine

# Ensure DB tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="InsightX: AI-Powered Data Analytics & Business Investigation Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for dev/production flexibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.exception_handler(InsightXException)
async def insightx_exception_handler(request: Request, exc: InsightXException):
    logger.warning(f"Domain Exception [{exc.status_code}]: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.detail}
    )

@app.get("/")
def root_endpoint():
    return {
        "platform": settings.APP_NAME,
        "status": "operational",
        "version": "1.0.0",
        "api_docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
