import os

DATA_DIR = os.getenv("DATA_DIR", "data")

# ---- Gemini (change the model ID to whatever your AI Studio account shows) ----
LLM_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
DAILY_LIMIT = int(os.getenv("GEMINI_DAILY_LIMIT", "20"))      # your free-tier cap
SAFETY_MARGIN = int(os.getenv("GEMINI_SAFETY_MARGIN", "2"))   # stop this many calls early

# ---- Local embeddings (no API calls) ----
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# ---- OCR ----
OCR_LANGS = os.getenv("OCR_LANGS", "eng+hin+mar")

# ---- Chunking / prompts ----
CHUNK_WORDS = 250
OVERLAP_WORDS = 40
EXTRACT_BATCH = 6          # schemes per criteria-extraction call
EXTRACT_WORDS = 1200       # max eligibility words sent per scheme
MAX_EXPLAIN = 8            # max schemes explained in the single search call
CHUNKS_PER_SCHEME = 3
CHUNK_CHARS_IN_PROMPT = 1000

# ---- Form vocabularies (the LLM must map scheme text onto these exact values) ----
STATES = ["Andhra Pradesh", "Bihar", "Delhi", "Gujarat", "Karnataka", "Kerala",
          "Madhya Pradesh", "Maharashtra", "Rajasthan", "Tamil Nadu", "Telangana",
          "Uttar Pradesh", "West Bengal", "Other"]
OCCUPATIONS = ["Farmer", "Student", "Unemployed", "Salaried", "Self-employed / Small business",
               "Street vendor", "Artisan / Craftsperson", "Daily wage labourer",
               "Homemaker", "Senior citizen / Retired"]
CATEGORIES = ["General", "OBC", "SC", "ST", "Minority"]
GENDERS = ["Male", "Female", "Other"]
