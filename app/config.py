import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY=os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAISS_PATH = os.path.join(BASE_DIR, "data", "faiss_index")
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FAISS_PATH, exist_ok=True)

# PDF & LLM config
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
TOP_K = 5
# SIMILARITY_THRESHOLD = 0.5
TEMPERATURE = 0.25
MAX_TOKENS = 3000
MAX_CONTEXT_CHARS = 8000
MAX_PAGES = 500
MAX_FILE_SIZE_MB = 50
MIN_PAGES = 1

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
