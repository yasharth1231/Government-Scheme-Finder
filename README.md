
# Government Scheme Finder

A RAG-based application that helps citizens identify government schemes they may be eligible for using information extracted from government scheme PDFs.

## Technologies Used

- **Python** – Core application logic
- **Streamlit** – User interface
- **Gemini API** – Eligibility criteria extraction and natural-language explanations
- **ChromaDB** – Vector database for storing and retrieving document embeddings
- **SQLite** – Database for storing scheme details, eligibility criteria, and application data
- **PyMuPDF** – PDF text extraction
- **Sentence Transformers** – Text embeddings for semantic search

## Installation

Clone the repository:

```bash
git clone https://github.com/yasharth1231/Government-Scheme-Finder.git
cd Government-Scheme-Finder
```

Create and activate a virtual environment:

**Windows (PowerShell):**

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Set your Gemini API key and model using PowerShell environment variables:

```powershell
$env:GEMINI_API_KEY="your_gemini_api_key"
$env:GEMINI_MODEL="your_supported_model_id"
```

Replace the placeholders with your Gemini API key and the model ID supported by your Google AI Studio account.

**Note:** These environment variables remain available only in the current PowerShell session. Set them again when opening a new terminal.

## Run the Application

Start the Streamlit application:

```powershell
streamlit run app.py
```

The application will open in your default browser.

## Application Workflow

1. **Admin:** Upload government scheme PDF documents.
2. **Document Processing:** Extract text from uploaded PDFs and generate embeddings.
3. **Eligibility Criteria Extraction:** Use Gemini to extract structured eligibility conditions from scheme documents.
4. **Review:** Review and update the extracted eligibility criteria.
5. **User Details:** Citizens enter details such as age, annual family income, state, occupation, gender, social category, disability status, and BPL card status.
6. **Scheme Matching:** The Python eligibility engine evaluates user information against the stored scheme criteria.
7. **Results:** Display potentially matching schemes with eligibility status, reasons, and relevant document information.

## Project Architecture

- **Document Processing:** Extracts text from uploaded government scheme PDFs using PyMuPDF.
- **RAG Pipeline:** Uses Sentence Transformers and ChromaDB for semantic retrieval of relevant document content.
- **Eligibility Engine:** Applies rule-based checks to identify matching government schemes.
- **Gemini Integration:** Extracts eligibility criteria and generates natural-language explanations.
- **SQLite Database:** Stores scheme information and structured eligibility criteria.
- **Streamlit Interface:** Provides administrative and citizen-facing functionality.

## OCR Support (For Scanned PDFs)

For scanned PDFs, install Tesseract OCR with the required language packs.

**Ubuntu:**

```bash
sudo apt install tesseract-ocr tesseract-ocr-hin tesseract-ocr-mar
```

**Windows:**

Install Tesseract using the UB-Mannheim installer. Select Hindi and Marathi language packs if required, and add Tesseract to the system PATH.

**macOS:**

```bash
brew install tesseract tesseract-lang
```

## Technologies Not Used

- Gradio
- OpenAI API
- Claude API
- Groq API
- Ollama
- FAISS
- LangChain
- LlamaIndex

The application uses a custom Python-based RAG pipeline instead of a RAG framework.

## Note

Eligibility results are indicative and based on the information and criteria available in the uploaded scheme documents. Final eligibility and approval are determined by the respective government authorities.
