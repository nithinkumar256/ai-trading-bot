from fastapi import FastAPI
from app.api.routes import router
from app.core.config import settings
from app.core.logger import logger

app = FastAPI(title=settings.APP_NAME)

app.include_router(router)

@app.on_event("startup")
def startup_event():
    logger.info("Starting AI Trading Bot...")

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down AI Trading Bot...")