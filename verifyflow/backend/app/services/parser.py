import pdfplumber
import pandas as pd
from docx import Document
from openai import OpenAI
import json
from io import BytesIO

client = OpenAI()

def parse_questionnaire(file_bytes: bytes, filename: str) -> list[str]:
    text = ""
    if filename.endswith(".pdf"):
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            text = "\n".join([p.extract_text() or "" for p in pdf.pages])
    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(BytesIO(file_bytes))
        return df.iloc[:, 0].dropna().tolist()  # assume first column = questions
    elif filename.endswith(".docx"):
        doc = Document(BytesIO(file_bytes))
        text = "\n".join([p.text for p in doc.paragraphs])

    # AI fallback for messy PDFs
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "Extract every question as a clean JSON array of strings."},
                  {"role": "user", "content": f"Text:\n{text}"}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)["questions"]

def parse_reference(file_bytes: bytes, filename: str) -> str:
    # same logic as above but return full text (no question splitting)
    ...
    # (I’ll give you the full function when you confirm this works)