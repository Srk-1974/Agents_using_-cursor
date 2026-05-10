"""Optional Cursor-powered helper utilities.

This module uses Cursor APIs when credentials are provided, and falls back
to deterministic local behavior otherwise.
"""

from __future__ import annotations

from typing import Dict

import requests

from config import Settings


class CursorCoordinator:
    """Provides optional prompt enrichment using Cursor APIs."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def build_linkedin_guidance(self, topic: str) -> Dict[str, str]:
        if not self.settings.cursor_api_key:
            return {
                "headline": f"{topic}: Practical insights",
                "tone": "professional and concise",
                "cta": "Share your perspective in the comments.",
            }

        try:
            response = requests.post(
                f"{self.settings.cursor_api_base_url.rstrip('/')}/v1/assist",
                headers={
                    "Authorization": f"Bearer {self.settings.cursor_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "task": "Create LinkedIn post guidance as JSON.",
                    "topic": topic,
                    "schema": {
                        "headline": "string",
                        "tone": "string",
                        "cta": "string",
                    },
                },
                timeout=self.settings.request_timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            data = payload.get("data", {})
            return {
                "headline": str(data.get("headline", topic)).strip(),
                "tone": str(data.get("tone", "professional and concise")).strip(),
                "cta": str(data.get("cta", "Share your perspective in the comments.")).strip(),
            }
        except (requests.RequestException, ValueError, TypeError):
            # Fallback keeps the app functional if Cursor integration is unavailable.
            return {
                "headline": f"{topic}: Practical insights",
                "tone": "professional and concise",
                "cta": "Share your perspective in the comments.",
            }
