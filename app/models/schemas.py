"""
Pydantic schemas for request/response validation.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


# ============================================================================
# Onboarding Schemas
# ============================================================================


class OnboardingRequest(BaseModel):
    """Request to onboard a new user with birth info."""

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    birthdate: date = Field(..., description="Birth date (YYYY-MM-DD)")
    birth_time: str | None = Field(
        None,
        pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$",
        description="Birth time in HH:MM format (24h)",
    )
    birth_place: str | None = Field(None, max_length=200, description="Birth city/location")

    @field_validator("birthdate")
    @classmethod
    def validate_birthdate(cls, v: date) -> date:
        """Ensure birthdate is in the past."""
        if v >= date.today():
            raise ValueError("Birthdate must be in the past")
        return v


class OnboardingResponse(BaseModel):
    """Response after successful onboarding."""

    user_id: str
    name: str
    sun_sign: str
    moon_sign: str | None = None
    message: str = "Welcome to Karmona! ✨"


# ============================================================================
# Daily Input Schemas
# ============================================================================

MoodType = Literal["sad", "neutral", "good", "great"]

ActionType = Literal[
    "helped",
    "argued",
    "loved",
    "meditated",
    "lied",
    "rested",
    "worked",
    "created",
    "learned",
    "exercised",
]


class DailyInputRequest(BaseModel):
    """User's daily mood and actions input."""

    # Note: user_id comes from JWT authentication, not from request body
    mood: MoodType
    actions: list[ActionType] = Field(..., min_length=1, max_length=10)
    note: str | None = Field(None, max_length=500, description="Optional personal note")


# ============================================================================
# Reflection Schemas
# ============================================================================


class ReflectionResponse(BaseModel):
    """AI-generated karma reflection."""

    karma_score: int = Field(..., ge=0, le=100, description="Karma score 0-100")
    reading: str = Field(..., description="2-3 sentence poetic reflection")
    rituals: list[str] = Field(
        ..., min_length=2, max_length=2, description="Two ritual suggestions"
    )
    report_id: str = Field(..., description="Database ID of the daily report")
    created_at: datetime


# ============================================================================
# History Schemas
# ============================================================================


class DailyReport(BaseModel):
    """A single daily report entry."""

    id: str
    user_id: str
    date: date
    mood: MoodType
    actions: list[ActionType]
    karma_score: int
    reading: str
    rituals: list[str]
    note: str | None = None
    created_at: datetime


class HistoryResponse(BaseModel):
    """User's karma history."""

    user_id: str
    reports: list[DailyReport] = Field(..., description="Last 7 days of reports")
    avg_karma_score: float | None = None


# ============================================================================
# User Profile Schema
# ============================================================================


class UserProfile(BaseModel):
    """User profile with astrology info."""

    id: str
    name: str
    email: str
    birthdate: date
    birth_time: str | None = None
    birth_place: str | None = None
    sun_sign: str
    moon_sign: str | None = None
    created_at: datetime


# ============================================================================
# Internal Schemas (not exposed via API)
# ============================================================================


class AstrologyData(BaseModel):
    """Calculated astrology data."""

    sun_sign: str
    moon_sign: str | None = None
    sun_position: float | None = None  # Degrees in zodiac
    moon_position: float | None = None
    planetary_summary: str | None = None  # Optional transit summary


class BedrockReflection(BaseModel):
    """Response from Bedrock LLM."""

    karma_score: int = Field(..., ge=0, le=100)
    reading: str
    rituals: list[str]
