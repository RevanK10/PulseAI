from typing import Any
from pydantic import BaseModel, Field


class PlanConcern(BaseModel):
    title: str = Field(max_length=80)
    desc: str = Field(max_length=300)


class NutritionGuidance(BaseModel):
    calories: int | None
    protein: str | None = Field(max_length=40)
    carbs: str | None = Field(max_length=40)
    fats: str | None = Field(max_length=40)
    notes: str = Field(max_length=300)


class HealthAssessment(BaseModel):
    assessment: str = Field(max_length=700)
    concerns: list[PlanConcern] = Field(max_length=3)
    urgent_care: str = Field(max_length=400)
    nutrition: NutritionGuidance
    workout: str = Field(max_length=400)
    limitations: str = Field(max_length=300)


class HealthPlanResponse(HealthAssessment):
    status: str
    parsed_markers: list[dict[str, Any]]
    image_processed: bool