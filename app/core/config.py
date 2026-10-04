# настройки приложения
import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL
DSN = os.getenv("DSN")

# Ollama / Embeddings
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/embed")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
EMBEDDING_DIMENSION = 768

# GigaChat
GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")
GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
GIGACHAT_BASE_URL = os.getenv("GIGACHAT_BASE_URL", "https://api.giga.chat/v1")
GIGACHAT_MODEL = os.getenv("GIGACHAT_MODEL", "GigaChat-2")