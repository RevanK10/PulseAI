import base64
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from schemas import HealthAssessment


SYSTEM_PROMPT = """You provide general wellness information, not medical diagnosis or treatment.
Analyze the supplied symptoms, pain rating, extracted lab values, and optional anonymized
photo. Give a concise assessment that identifies plausible explanations and explicitly
connects them to the supplied evidence; do not merely restate the input. State uncertainty
and what important context is missing. For photos, describe only visible posture or
movement observations and never infer a diagnosis or internal condition.

Treat the pain score as the user's own report: do not label it mild, moderate, or severe
unless the user provides that interpretation. Describe possible patterns cautiously, not
as confirmed diagnoses or proof of a structural injury.

Flag emergency warning signs only when supported by the reported symptoms. Recommend
urgent medical care when appropriate, and tell the user to seek emergency help for
severe or rapidly worsening symptoms. Never recommend prescription changes.

Do not call lab results abnormal unless a reference range and units support that conclusion.
Do not invent age, sex, height, weight, medical history, lab values, or goals. Only provide
numeric calorie or macro targets when the supplied information is sufficient; otherwise
set those values to null and explain what is missing in nutrition.notes. Keep exercise
recommendations conservative and advise stopping movements that worsen pain.

Return only a practical, readable response matching the JSON schema. Keep every field
concise: one or two sentences. Include a brief evidence-based rationale, not hidden
chain-of-thought. Make clear this is not a substitute for a clinician."""


class ModelUnavailableError(Exception):
    pass


class ModelResponseError(Exception):
    pass


def generate_assessment(
    symptoms: str,
    pain_scale: int,
    parsed_markers: list[dict],
    anonymized_image: bytes | None = None,
) -> HealthAssessment:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    if anonymized_image is not None:
        model = os.getenv("OLLAMA_VISION_MODEL", "qwen2.5vl:3b")
    else:
        model = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

    user_content = {
        "symptoms": symptoms,
        "pain_scale": pain_scale,
        "lab_markers": parsed_markers,
        "image_included": anonymized_image is not None,
    }
    message: dict[str, object] = {
        "role": "user",
        "content": json.dumps(user_content),
    }
    if anonymized_image is not None:
        message["images"] = [base64.b64encode(anonymized_image).decode("ascii")]

    request_body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                message,
            ],
            "format": HealthAssessment.model_json_schema(),
            "stream": False,
            "keep_alive": "10m",
            "options": {
                "temperature": 0.2,
                "num_ctx": 2048,
                "num_predict": 768,
            },
        }
    ).encode("utf-8")
    request = Request(
        f"{base_url}/api/chat",
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=300) as response:
            payload = json.loads(response.read())
    except HTTPError as error:
        if error.code == 404:
            raise ModelUnavailableError(
                f"Ollama could not find model '{model}'. Pull it with `ollama pull {model}`."
            ) from error
        raise ModelResponseError(
            f"Ollama returned HTTP {error.code} while generating the assessment."
        ) from error
    except (URLError, TimeoutError) as error:
        raise ModelUnavailableError(
            "Could not connect to Ollama at "
            f"{base_url}. Start Ollama and make sure model '{model}' is installed."
        ) from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ModelResponseError("Ollama returned an invalid JSON response.") from error

    message_payload = payload.get("message") if isinstance(payload, dict) else None
    content = (
        message_payload.get("content")
        if isinstance(message_payload, dict)
        else None
    )
    if not isinstance(content, str):
        raise ModelResponseError("Ollama response did not contain assessment content.")

    try:
        return HealthAssessment.model_validate_json(content)
    except (ValidationError, ValueError) as error:
        if isinstance(error, ValidationError):
            details = "; ".join(
                f"{'.'.join(map(str, issue['loc']))}: {issue['msg']}"
                for issue in error.errors(include_input=False)
            )
            message = (
                "The local model returned an assessment that did not match the "
                f"required format: {details}"
            )
        else:
            message = "The local model returned invalid assessment JSON."
        raise ModelResponseError(
            message
        ) from error
