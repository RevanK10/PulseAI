const API_BASE_URL = "/backend-api";

export interface HealthPlanRequest {
  symptoms: string;
  painScale: number;
  bodyPhoto?: File | null;
  bloodTestPdf?: File | null;
}

export interface HealthPlan {
  status: string;
  assessment: string;
  concerns: { title: string; desc: string }[];
  urgent_care: string;
  nutrition: {
    calories: number | null;
    protein: string | null;
    carbs: string | null;
    fats: string | null;
    notes: string;
  };
  workout: string;
  limitations: string;
  parsed_markers: { marker_name: string; value: number; unit: string }[];
  image_processed: boolean;
}

export async function fetchHealthPlan(data: HealthPlanRequest): Promise<HealthPlan> {
  const formData = new FormData();
  formData.append("symptoms", data.symptoms);
  formData.append("pain_scale", data.painScale.toString());

  if (data.bodyPhoto) {
    formData.append("body_photo", data.bodyPhoto);
  }
  if (data.bloodTestPdf) {
    formData.append("blood_test_pdf", data.bloodTestPdf);
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/health/generate-plan`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const responseBody = await response.json().catch(() => null);
    const detail =
      typeof responseBody?.detail === "string"
        ? responseBody.detail
        : responseBody
          ? JSON.stringify(responseBody)
          : response.statusText || "No response body";
    throw new Error(
      `API error (${response.status}): ${detail}`,
    );
  }

  return response.json();
}