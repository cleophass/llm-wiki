import logging

import mlflow
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import conversations, wiki
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

mlflow.set_tracking_uri(settings.mlflow_tracking_uri)

app = FastAPI(
    title="LLM Wiki Backend",
    description="Ingests documents, builds a structured wiki, and answers questions.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(conversations.router)
app.include_router(wiki.router)
