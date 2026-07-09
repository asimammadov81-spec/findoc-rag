"""
app.py - FastAPI tətbiqi

FastAPI konseptleri:
  - FastAPI()     : ana tətbiq obyekti
  - lifespan      : startup/shutdown hadisesi
  - app.state     : paylaşılan vəziyyət (pipeline, llm)
  - include_router: route-ları ayrı fayldan qoş
  - CORS          : browser-dan API-ya icazə
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.llm.client import LLMClient
from src.rag.pipeline import RAGPipeline

from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: RAG pipeline ve LLM-i bir defe yarat, app.state-de saxla.
    Shutdown: resursları sərbəst burax.
    """
    print("[App] Bashlayir...")
    app.state.pipeline = RAGPipeline(persist_dir="./chroma_db")
    app.state.llm = LLMClient()
    print("[App] Hazirdir.")
    yield
    # Shutdown
    print("[App] Dayanir.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="FinDoc RAG API",
        description="Maliyye senedleri uzerinde sual-cavab sistemi",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS — browser-dan cagirishlar ucun
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Route-ları qoş
    app.include_router(router, prefix="/api/v1")

    return app


app = create_app()
