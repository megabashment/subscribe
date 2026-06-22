from __future__ import annotations

import logging
import warnings
import os

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import health, transcribe
from subscribe.utils.logging import setup_logging

setup_logging("INFO")
logger = logging.getLogger(__name__)

app = FastAPI(title="SubScribe API", version="0.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8511", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(transcribe.router)

logger.info("SubScribe API ready")
