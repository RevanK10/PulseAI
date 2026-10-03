import re
import io
from typing import List, Dict, Any
import pdfplumber

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extracts raw text from an uploaded PDF blood test report."""
    extracted_text = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
    return extracted_text

def parse_blood_markers(text: str) -> List[Dict[str, Any]]:
    """Uses regex patterns to parse key biomarkers (Vitamin D, Glucose, Cholesterol)."""
    markers = []
    
    patterns = {
        "Vitamin D": r"Vitamin\s*D[^\d]*(\d+\.?\d*)\s*(ng/mL|nmol/L)?",
        "Glucose": r"Glucose[^\d]*(\d+\.?\d*)\s*(mg/dL)?",
        "Cholesterol": r"Cholesterol[^\d]*(\d+\.?\d*)\s*(mg/dL)?"
    }

    for marker_name, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            markers.append({
                "marker_name": marker_name,
                "value": float(match.group(1)),
                "unit": match.group(2) if len(match.groups()) > 1 else "N/A"
            })

    return markers