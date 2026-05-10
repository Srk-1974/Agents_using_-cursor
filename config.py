"""Centralized configuration loading and validation."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    linkedin_client_id: str
    linkedin_client_secret: str
    linkedin_access_token: str
    linkedin_refresh_token: str
    youtube_api_key: str
    request_timeout_seconds: int
    cursor_api_key: str
    cursor_api_base_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            linkedin_client_id=os.getenv("LINKEDIN_CLIENT_ID", "").strip(),
            linkedin_client_secret=os.getenv("LINKEDIN_CLIENT_SECRET", "").strip(),
            linkedin_access_token=os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip(),
            linkedin_refresh_token=os.getenv("LINKEDIN_REFRESH_TOKEN", "").strip(),
            youtube_api_key=os.getenv("YOUTUBE_API_KEY", "").strip(),
            request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20")),
            cursor_api_key=os.getenv("CURSOR_API_KEY", "").strip(),
            cursor_api_base_url=os.getenv("CURSOR_API_BASE_URL", "https://api.cursor.com").strip(),
        )

    def validate_for_linkedin(self) -> None:
        missing = []
        if not self.linkedin_access_token:
            missing.append("LINKEDIN_ACCESS_TOKEN")
        if not self.linkedin_client_id:
            missing.append("LINKEDIN_CLIENT_ID")
        if not self.linkedin_client_secret:
            missing.append("LINKEDIN_CLIENT_SECRET")
        if missing:
            raise ValueError(f"Missing LinkedIn configuration: {', '.join(missing)}")

    def validate_for_youtube(self) -> None:
        if not self.youtube_api_key:
            raise ValueError("Missing YouTube configuration: YOUTUBE_API_KEY")
