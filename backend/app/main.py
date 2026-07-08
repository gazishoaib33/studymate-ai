from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered study assistant -- RAG chat, summarizer, quizzes, flashcards over lecture PDFs.",
    version="0.1.0",
)

# Dev-friendly CORS: any localhost port, since Vite may start on 5173, 5174, etc.
# depending on what's already running. Tighten this to one specific origin
# before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} API is running. See /docs for the API reference."}
