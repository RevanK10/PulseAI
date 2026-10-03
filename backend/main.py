import asyncio
import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from schemas import HealthPlanResponse
from services.assessment import (
    ModelResponseError,
    ModelUnavailableError,
    generate_assessment,
)
from services.ocr import extract_text_from_pdf, parse_blood_markers
from services.vision import anonymize_patient_image

app = FastAPI(title="PulseAI Engine", version="1.0.0")

allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
codespace_name = os.getenv("CODESPACE_NAME")
forwarding_domain = os.getenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN")
if codespace_name and forwarding_domain:
    allowed_origins.append(f"https://{codespace_name}-3000.{forwarding_domain}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
async def health_check():
    return {"status": "online", "service": "PulseAI Core API"}

@app.post("/api/v1/health/generate-plan", response_model=HealthPlanResponse)
async def generate_plan(
    symptoms: str = Form(..., min_length=1, max_length=4000),
    pain_scale: int = Form(5, ge=0, le=10),
    body_photo: Optional[UploadFile] = File(None),
    blood_test_pdf: Optional[UploadFile] = File(None)
):
    parsed_markers = []
    anonymized_image = None
    image_processed = False

    if blood_test_pdf:
        pdf_bytes = await blood_test_pdf.read(10 * 1024 * 1024 + 1)
        if len(pdf_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="The PDF must be 10 MB or smaller.")
        raw_text = extract_text_from_pdf(pdf_bytes)
        parsed_markers = parse_blood_markers(raw_text)

    if body_photo:
        image_bytes = await body_photo.read(10 * 1024 * 1024 + 1)
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="The photo must be 10 MB or smaller.")
        anonymized_image = anonymize_patient_image(image_bytes)
        image_processed = True

    try:
        assessment = await asyncio.to_thread(
            generate_assessment,
            symptoms,
            pain_scale,
            parsed_markers,
            anonymized_image,
        )
    except ModelUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ModelResponseError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    return {
        **assessment.model_dump(),
        "status": "success",
        "parsed_markers": parsed_markers,
        "image_processed": image_processed,
    }