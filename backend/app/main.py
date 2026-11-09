from fastapi import FastAPI

from backend.app.core.config import settings

from backend.app.api.routes import (
    chat,
    health,
    documents,
    analysis,
    reports,
    audit
)

from contextlib import asynccontextmanager

from backend.app.database.connection import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AEGIS ENGINE - Private Offline-First "
        "Agentic AI Workbench for Industrial Operations."
    ),
    lifespan=lifespan
)


app.include_router(health.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(reports.router)
app.include_router(audit.router)


@app.get("/")
async def root():

    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "Welcome to AEGIS ENGINE.",
        "documentation": "/docs"
    }