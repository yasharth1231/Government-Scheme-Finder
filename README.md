# Government Scheme Finder (Gemini + Streamlit + ChromaDB + SQLite)

## Install
    pip install -r requirements.txt

OCR (only needed for scanned PDFs): install the Tesseract app plus language packs.
- Ubuntu: sudo apt install tesseract-ocr tesseract-ocr-hin tesseract-ocr-mar
- Windows: UB-Mannheim installer (tick Hindi and Marathi), add it to PATH
- macOS: brew install tesseract tesseract-lang

## Run
    export GEMINI_API_KEY="your_key"
    export GEMINI_MODEL="your-model-id"     # exact ID from AI Studio
    streamlit run app.py

## Workflow
1. Admin tab: upload PDFs → Index PDFs (0 API calls)
2. Admin tab: Extract criteria (6 schemes per call, once per scheme)
3. Review tab: check/fix the extracted rules
4. Find tab: fill the form → results

## API budget (20/day)
- Indexing, retrieval, rules: 0 calls (local embeddings, ChromaDB, Python)
- Criteria extraction: 1 call per 6 new schemes, saved forever
- Each new search: 1 call; repeated identical profiles: 0 (cache)
- A counter in SQLite stops calls at DAILY_LIMIT - SAFETY_MARGIN; after that the app shows rule-based results
