import io
import json
from fastapi import APIRouter, UploadFile, File
from pypdf import PdfReader
from docx import Document
from ..core.ModelIntegrations.gpt import OpenAIClient

router = APIRouter()

# -----------------------------
# PDF extraction
# -----------------------------
def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF using PyPDF."""
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            extracted = page.extract_text() or ""
            text += extracted + "\n"
        return text.strip()
    except Exception as e:
        print("PDF extraction error:", e)
        return ""

# -----------------------------
# DOCX extraction
# -----------------------------
def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX Word file."""
    try:
        file_stream = io.BytesIO(file_bytes)
        document = Document(file_stream)
        text = "\n".join([para.text for para in document.paragraphs])
        return text.strip()
    except Exception as e:
        print("DOCX extract error:", e)
        return ""

# -----------------------------
# LLM Analysis (JSON-safe)
# -----------------------------
async def analyze_resume_text(text: str):
    """Send extracted text to OpenAI and guarantee JSON output."""
    prompt = f"""
    You are a professional career analyst.

    Analyze the resume text below and output ONLY valid JSON:

    {{
      "summary": "4–5 sentence summary of their professional background",
      "suggested_role": "One of: Data Analyst, Data Scientist, Data Engineer, Machine Learning Engineer"
    }}

    Resume Text:
    {text}

    Output only JSON. No explanations.
    """
    client = OpenAIClient()
    raw = await client._chat([
        {"role": "user", "content": prompt}
    ])

    print("LLM RAW:", raw)

    # Try direct JSON load
    try:
        return json.loads(raw)
    except:
        pass

    # Try to recover JSON substring
    try:
        cleaned = raw[raw.index("{"): raw.rindex("}") + 1]
        return json.loads(cleaned)
    except Exception as e:
        print("JSON recovery failed:", e)
        return {
            "summary": "Could not parse AI output.",
            "suggested_role": "Unknown"
        }

# -----------------------------
# Route
# -----------------------------
@router.post("/parse", tags=["resume"])
async def parse_resume(file: UploadFile = File(...)):
    file_bytes = await file.read()
    filename = file.filename.lower()

    # Determine file type
    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    elif filename.endswith(".docx") or filename.endswith(".doc"):
        text = extract_text_from_docx(file_bytes)
    else:
        return {
            "summary": "Unsupported file type.",
            "suggested_role": "Unknown"
        }

    if not text or len(text) < 30:
        return {
            "summary": "Could not extract meaningful text from the resume.",
            "suggested_role": "Unknown"
        }

    # Analyze using LLM
    return await analyze_resume_text(text)
