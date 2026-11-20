"""PDF -> text (with OCR fallback) -> section-aware chunks."""
import io, re, hashlib
import fitz  # PyMuPDF
from config import *
import pytesseract; pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

HEADINGS = {
    "eligibility": r"eligib|who can apply|beneficiar|target group|qualif",
    "documents": r"document|required papers|proof",
    "apply": r"how to apply|application process|procedure|apply",
    "benefits": r"benefit|assistance|incentive|subsid|financial",
}


def _ocr_page(page):
    import pytesseract
    from PIL import Image
    img = Image.open(io.BytesIO(page.get_pixmap(dpi=200).tobytes("png")))
    try:
        return pytesseract.image_to_string(img, lang=OCR_LANGS)
    except pytesseract.TesseractError:      # language pack missing -> English only
        return pytesseract.image_to_string(img, lang="eng")


def extract_text(data: bytes):
    """Returns (text, ocr_pages, ocr_error)."""
    doc = fitz.open(stream=data, filetype="pdf")
    parts, ocr_pages, ocr_error = [], 0, None
    for page in doc:
        text = page.get_text()
        if len(text.strip()) < 30:           # looks scanned
            try:
                text = _ocr_page(page)
                ocr_pages += 1
            except Exception as e:           # Tesseract not installed
                ocr_error = str(e)
        parts.append(text)
    return "\n".join(parts), ocr_pages, ocr_error


def _heading_label(line):
    head = line.split(":", 1)[0]
    if len(head.split()) > 8:
        return None, line
    looks_like_heading = line.endswith(":") or ":" in line or head.isupper() or head.istitle()
    if not looks_like_heading:
        return None, line
    low = head.lower()
    for label, pat in HEADINGS.items():
        if re.search(pat, low):
            rest = line.split(":", 1)[1].strip() if ":" in line else ""
            return label, rest
    return None, line


def split_sections(text):
    sections, label, buf = [], "general", []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        new_label, rest = _heading_label(line)
        if new_label:
            if buf:
                sections.append((label, " ".join(buf)))
            label, buf = new_label, ([rest] if rest else [])
        else:
            buf.append(line)
    if buf:
        sections.append((label, " ".join(buf)))
    return sections


def make_chunks(text):
    chunks, step = [], CHUNK_WORDS - OVERLAP_WORDS
    for label, body in split_sections(text):
        words = body.split()
        for i in range(0, max(len(words), 1), step):
            piece = " ".join(words[i:i + CHUNK_WORDS])
            if piece.strip():
                chunks.append((label, piece))
    return chunks


def eligibility_text(text):
    """Text sent to the criteria extractor: eligibility sections, else the start of the doc."""
    elig = " ".join(b for l, b in split_sections(text) if l == "eligibility")
    words = (elig if len(elig.split()) > 30 else text).split()
    return " ".join(words[:EXTRACT_WORDS])


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def text_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]
