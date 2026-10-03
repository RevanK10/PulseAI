import base64
import json
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import URLError

from services.assessment import (
    ModelUnavailableError,
    generate_assessment,
)


def model_response(content: dict) -> MagicMock:
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(
        {"message": {"content": json.dumps(content)}}
    ).encode()
    return response


class GenerateAssessmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.content = {
            "assessment": "A cautious interpretation with a brief rationale.",
            "concerns": [{"title": "Possible pattern", "desc": "Why it may fit."}],
            "urgent_care": "Seek care for severe or worsening symptoms.",
            "nutrition": {
                "calories": None,
                "protein": None,
                "carbs": None,
                "fats": None,
                "notes": "More profile information is needed.",
            },
            "workout": "Avoid movements that worsen pain.",
            "limitations": "This is not a diagnosis.",
        }

    @patch("services.assessment.urlopen")
    def test_returns_validated_assessment_and_requests_structured_output(self, mock_urlopen):
        mock_urlopen.return_value = model_response(self.content)

        result = generate_assessment("back pain", 3, [])

        self.assertEqual(result.assessment, self.content["assessment"])
        request = mock_urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(payload["model"], "qwen2.5:1.5b")
        self.assertEqual(payload["format"]["type"], "object")
        self.assertEqual(payload["options"]["num_ctx"], 2048)
        self.assertEqual(payload["options"]["num_predict"], 768)

    @patch("services.assessment.urlopen", side_effect=URLError("offline"))
    def test_reports_unavailable_local_model(self, _mock_urlopen):
        with self.assertRaisesRegex(ModelUnavailableError, "Could not connect to Ollama"):
            generate_assessment("back pain", 3, [])

    @patch("services.assessment.urlopen")
    def test_sends_optional_image_to_local_vision_model(self, mock_urlopen):
        mock_urlopen.return_value = model_response(self.content)
        image = b"anonymized-image-bytes"

        generate_assessment("back pain", 3, [], image)

        payload = json.loads(mock_urlopen.call_args.args[0].data)
        user_message = payload["messages"][1]
        self.assertEqual(payload["model"], "qwen2.5vl:3b")
        self.assertEqual(user_message["images"], [base64.b64encode(image).decode("ascii")])


if __name__ == "__main__":
    unittest.main()
