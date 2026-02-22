import os
from dotenv import load_dotenv


load_dotenv()


OLLAMA_DEFAULT_MODEL = os.getenv("OLLAMA_DEFAULT_MODEL", "phi3")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_CLOUD_BASE_URL = os.getenv("OLLAMA_CLOUD_BASE_URL", "https://ollama.com")
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "http://localhost:5050")
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "LLMs comparison tool and router")
LMSTUDIO_URL = os.getenv("LMSTUDIO_URL", "http://localhost:1234/v1")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")

MAX_CONTEXT_MESSAGES = int(os.getenv("MAX_CONTEXT_MESSAGES", "12"))
COMPARE_MAX_WORKERS = int(os.getenv("COMPARE_MAX_WORKERS", "2"))
ENABLE_BAC_LOGS = os.getenv("ENABLE_BAC_LOGS", "false").lower() == "true"
APP_DEBUG = os.getenv("APP_DEBUG", "false").lower() == "true"
