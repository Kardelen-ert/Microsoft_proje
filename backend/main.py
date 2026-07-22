"""Application entrypoint for the local rail systems RAG assistant."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # CORS kütüphanesi eklendi

from app.core.constants import APP_NAME
from app.db.database import initialize_database
from app.api.routes import router
from app.utils.logger import configure_logging

app = FastAPI(
    title=APP_NAME,
    version="0.1.0",
    description="Offline, enterprise-grade diagnostic assistant backend.",
)

# Tüm cihazlardan (Flutter Web/Android vs.) gelen isteklere izin veren CORS ayarı
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.on_event("startup")
def on_startup() -> None:
    """Prepare local infras0tructure required by the backend."""

    configure_logging()
    initialize_database()


@app.get("/")
def root() -> dict[str, str]:
    """Small root endpoint for quick manual checks."""

    return {"message": "Backend is running"}