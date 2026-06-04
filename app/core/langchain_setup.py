import os
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

# Configure LangSmith on module import
if settings.LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT

def get_gemini_flash(streaming: bool = True):
    """Gemini 1.5 Flash for fast analysis and tool usage"""
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.1,
        streaming=streaming
    )

def get_gemini_vision(streaming: bool = True):
    """Gemini 1.5 Pro for vision-intensive tasks and deep reasoning"""
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.1,
        streaming=streaming
    )
