"""Storage layer: SQLite (criteria, quota, cache) + ChromaDB (vectors) + local embeddings."""
import os, json, sqlite3, hashlib, datetime
import chromadb
from fastembed import TextEmbedding
from config import *

_conn = None
_col = None
_embedder = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS schemes(
  scheme_id TEXT PRIMARY KEY, name TEXT, text_hash TEXT,
  elig_text TEXT, criteria_json TEXT, ocr_pages INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS usage(day TEXT PRIMARY KEY, count INTEGER);
CREATE TABLE IF NOT EXISTS cache(key TEXT PRIMARY KEY, value TEXT, created TEXT);
"""


def db():
    global _conn
    if _conn is None:
        os.makedirs(DATA_DIR, exist_ok=True)
        _conn = sqlite3.connect(os.path.join(DATA_DIR, "schemes.db"), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript(SCHEMA)
    return _conn


def collection():
    global _col
    if _col is None:
        client = chromadb.PersistentClient(path=os.path.join(DATA_DIR, "chroma"))
        _col = client.get_or_create_collection("chunks", metadata={"hnsw:space": "cosine"})
    return _col


def embed(texts):
    global _embedder
    if _embedder is None:
        _embedder = TextEmbedding(model_name=EMBED_MODEL)
    return [v.tolist() for v in _embedder.embed(texts)]


# ---------------- schemes ----------------
def get_scheme(sid):
    row = db().execute("SELECT * FROM schemes WHERE scheme_id=?", (sid,)).fetchone()
    return dict(row) if row else None


def list_schemes():
    rows = db().execute("SELECT * FROM schemes ORDER BY name").fetchall()
    return [dict(r) for r in rows]      # plain dicts: Streamlit can copy/pickle these


def upsert_scheme(sid, name, text_hash, elig_text, ocr_pages):
    db().execute(
        "INSERT INTO schemes(scheme_id,name,text_hash,elig_text,criteria_json,ocr_pages) VALUES(?,?,?,?,NULL,?) "
        "ON CONFLICT(scheme_id) DO UPDATE SET name=excluded.name,text_hash=excluded.text_hash,"
        "elig_text=excluded.elig_text,criteria_json=NULL,ocr_pages=excluded.ocr_pages",
        (sid, name, text_hash, elig_text, ocr_pages))
    db().commit()


def save_criteria(sid, criteria: dict):
    db().execute("UPDATE schemes SET criteria_json=? WHERE scheme_id=?", (json.dumps(criteria), sid))
    db().commit()


def rename_scheme(sid, new_name):
    db().execute("UPDATE schemes SET name=? WHERE scheme_id=?", (new_name.strip(), sid))
    db().commit()


def reset_all_criteria():
    db().execute("UPDATE schemes SET criteria_json=NULL")
    db().commit()


def add_chunks(sid, name, chunks):
    """chunks: list of (section_label, text). Replaces any old chunks for this scheme."""
    col = collection()
    col.delete(where={"scheme_id": sid})
    if not chunks:
        return
    texts = [f"[{name}] {t}" for _, t in chunks]
    col.add(ids=[f"{sid}-{i}" for i in range(len(texts))],
            documents=texts,
            embeddings=embed(texts),
            metadatas=[{"scheme_id": sid, "section": s} for s, _ in chunks])


def search_scheme(sid, query_vec, n):
    try:
        r = collection().query(query_embeddings=[query_vec], n_results=n, where={"scheme_id": sid})
        return r["documents"][0]
    except Exception:
        return []


# ---------------- quota ----------------
def _today():
    return datetime.date.today().isoformat()


def calls_used():
    row = db().execute("SELECT count FROM usage WHERE day=?", (_today(),)).fetchone()
    return row["count"] if row else 0


def calls_left():
    return max(0, DAILY_LIMIT - SAFETY_MARGIN - calls_used())


def record_call():
    db().execute("INSERT INTO usage(day,count) VALUES(?,1) "
                 "ON CONFLICT(day) DO UPDATE SET count=count+1", (_today(),))
    db().commit()


# ---------------- cache ----------------
def data_version():
    rows = db().execute("SELECT scheme_id,name,text_hash,criteria_json FROM schemes ORDER BY scheme_id").fetchall()
    return hashlib.sha256(json.dumps([tuple(r) for r in rows]).encode()).hexdigest()[:16]


def cache_key(profile):
    raw = json.dumps(profile, sort_keys=True) + data_version() + LLM_MODEL
    return hashlib.sha256(raw.encode()).hexdigest()


def cache_get(key):
    row = db().execute("SELECT value FROM cache WHERE key=?", (key,)).fetchone()
    return json.loads(row["value"]) if row else None


def cache_put(key, value):
    db().execute("INSERT OR REPLACE INTO cache(key,value,created) VALUES(?,?,?)",
                 (key, json.dumps(value), datetime.datetime.now().isoformat()))
    db().commit()