"""
Supabase database service for user data and daily reports.
"""

from datetime import date, datetime
from typing import Any

from supabase import create_client, Client

from app.core.config import settings
from app.models.schemas import UserProfile, DailyReport, MoodType, ActionType


class SupabaseService:
    """Service for interacting with Supabase database."""

    def __init__(self) -> None:
        """Initialize Supabase client."""
        self.client: Client = create_client(
            settings.supabase_url, settings.supabase_service_role_key
        )

    async def create_user(
        self,
        name: str,
        email: str,
        birthdate: date,
        birth_time: str | None,
        birth_place: str | None,
        sun_sign: str,
        moon_sign: str | None,
        user_id: str | None = None,
    ) -> UserProfile:
        """Create a new user in the database."""
        data = {
            "name": name,
            "email": email,
            "birthdate": birthdate.isoformat(),
            "birth_time": birth_time,
            "birth_place": birth_place,
            "sun_sign": sun_sign,
            "moon_sign": moon_sign,
        }
        
        # If user_id is provided (from auth), use it
        if user_id:
            data["id"] = user_id

        response = self.client.table("users").insert(data).execute()

        if not response.data:
            raise Exception("Failed to create user")

        user_data = response.data[0]
        return UserProfile(
            id=user_data["id"],
            name=user_data["name"],
            email=user_data["email"],
            birthdate=datetime.fromisoformat(user_data["birthdate"]).date(),
            birth_time=user_data.get("birth_time"),
            birth_place=user_data.get("birth_place"),
            sun_sign=user_data["sun_sign"],
            moon_sign=user_data.get("moon_sign"),
            created_at=datetime.fromisoformat(user_data["created_at"]),
        )

    async def get_user(self, user_id: str) -> UserProfile | None:
        """Get user by ID."""
        response = self.client.table("users").select("*").eq("id", user_id).execute()

        if not response.data:
            return None

        user_data = response.data[0]
        return UserProfile(
            id=user_data["id"],
            name=user_data["name"],
            email=user_data["email"],
            birthdate=datetime.fromisoformat(user_data["birthdate"]).date(),
            birth_time=user_data.get("birth_time"),
            birth_place=user_data.get("birth_place"),
            sun_sign=user_data["sun_sign"],
            moon_sign=user_data.get("moon_sign"),
            created_at=datetime.fromisoformat(user_data["created_at"]),
        )

    async def create_daily_report(
        self,
        user_id: str,
        report_date: date,
        mood: MoodType,
        actions: list[ActionType],
        karma_score: int,
        reading: str,
        rituals: list[str],
        note: str | None = None,
    ) -> DailyReport:
        """Create a daily report entry."""
        data = {
            "user_id": user_id,
            "date": report_date.isoformat(),
            "mood": mood,
            "actions": actions,
            "karma_score": karma_score,
            "reading": reading,
            "rituals": rituals,
            "note": note,
        }

        response = self.client.table("daily_reports").insert(data).execute()

        if not response.data:
            raise Exception("Failed to create daily report")

        report_data = response.data[0]
        return self._map_to_daily_report(report_data)

    async def get_user_history(self, user_id: str, limit: int = 7) -> list[DailyReport]:
        """Get user's recent daily reports."""
        response = (
            self.client.table("daily_reports")
            .select("*")
            .eq("user_id", user_id)
            .order("date", desc=True)
            .limit(limit)
            .execute()
        )

        return [self._map_to_daily_report(report) for report in response.data]

    async def get_report_by_date(self, user_id: str, report_date: date) -> DailyReport | None:
        """Get a specific report by user and date."""
        response = (
            self.client.table("daily_reports")
            .select("*")
            .eq("user_id", user_id)
            .eq("date", report_date.isoformat())
            .execute()
        )

        if not response.data:
            return None

        return self._map_to_daily_report(response.data[0])

    def _map_to_daily_report(self, data: dict[str, Any]) -> DailyReport:
        """Map database row to DailyReport model."""
        return DailyReport(
            id=data["id"],
            user_id=data["user_id"],
            date=datetime.fromisoformat(data["date"]).date(),
            mood=data["mood"],
            actions=data["actions"],
            karma_score=data["karma_score"],
            reading=data["reading"],
            rituals=data["rituals"],
            note=data.get("note"),
            created_at=datetime.fromisoformat(data["created_at"]),
        )
