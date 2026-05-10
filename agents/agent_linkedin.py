"""LinkedIn publishing agent implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import requests

from config import Settings


LINKEDIN_MAX_CHARACTERS = 3000


@dataclass
class LinkedInResult:
    success: bool
    message: str
    post_url: str
    content: str


class LinkedInPublisherAgent:
    def __init__(self, settings: Settings):
        self.settings = settings

    def publish_post(self, topic: str, guidance: Dict[str, str]) -> LinkedInResult:
        self.settings.validate_for_linkedin()

        post_body = self._build_post(topic=topic, guidance=guidance)
        access_token = self.settings.linkedin_access_token

        try:
            member_id = self._fetch_member_id(access_token)
            post_id = self._create_post(member_id=member_id, access_token=access_token, post_body=post_body)
            post_url = f"https://www.linkedin.com/feed/update/{post_id}/" if post_id else ""
            return LinkedInResult(
                success=True,
                message="LinkedIn post published successfully.",
                post_url=post_url,
                content=post_body,
            )
        except requests.HTTPError as http_error:
            if http_error.response is not None and http_error.response.status_code == 401:
                refreshed = self._refresh_access_token()
                if refreshed:
                    member_id = self._fetch_member_id(refreshed)
                    post_id = self._create_post(member_id=member_id, access_token=refreshed, post_body=post_body)
                    post_url = f"https://www.linkedin.com/feed/update/{post_id}/" if post_id else ""
                    return LinkedInResult(
                        success=True,
                        message="LinkedIn post published after token refresh.",
                        post_url=post_url,
                        content=post_body,
                    )
            return LinkedInResult(
                success=False,
                message=f"LinkedIn API error: {http_error}",
                post_url="",
                content=post_body,
            )
        except (requests.RequestException, ValueError, KeyError, TypeError) as error:
            return LinkedInResult(
                success=False,
                message=f"LinkedIn publish failed: {error}",
                post_url="",
                content=post_body,
            )

    def _build_post(self, topic: str, guidance: Dict[str, str]) -> str:
        # Keep structure clear and concise to match LinkedIn best practices.
        headline = guidance.get("headline", topic)
        tone = guidance.get("tone", "professional and concise")
        cta = guidance.get("cta", "What is your take?")
        text = (
            f"{headline}\n\n"
            f"Today I explored {topic} with a {tone} lens.\n\n"
            "Key takeaways:\n"
            "- Why this matters now\n"
            "- Practical opportunities for teams\n"
            "- Risks and implementation pitfalls to avoid\n\n"
            f"{cta}\n\n"
            f"#AI #{topic.replace(' ', '')}"
        )
        return text[:LINKEDIN_MAX_CHARACTERS]

    def _fetch_member_id(self, access_token: str) -> str:
        headers = {"Authorization": f"Bearer {access_token}"}
        timeout = self.settings.request_timeout_seconds

        # Support both older and newer profile endpoints.
        for profile_url in ("https://api.linkedin.com/v2/userinfo", "https://api.linkedin.com/v2/me"):
            response = requests.get(profile_url, headers=headers, timeout=timeout)
            if response.status_code == 404:
                continue
            response.raise_for_status()
            payload = response.json()
            member_id = payload.get("sub") or payload.get("id")
            if not member_id:
                raise ValueError("Unable to extract LinkedIn member id from profile response.")
            return member_id

        raise ValueError("Unable to fetch LinkedIn member profile.")

    def _create_post(self, member_id: str, access_token: str, post_body: str) -> str:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        payload = {
            "author": f"urn:li:person:{member_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": post_body},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }
        response = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=headers,
            json=payload,
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        # LinkedIn commonly returns post URN in x-restli-id header.
        return response.headers.get("x-restli-id", "")

    def _refresh_access_token(self) -> str:
        if not self.settings.linkedin_refresh_token:
            return ""

        response = requests.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.settings.linkedin_refresh_token,
                "client_id": self.settings.linkedin_client_id,
                "client_secret": self.settings.linkedin_client_secret,
            },
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        token = payload.get("access_token", "")
        return str(token)
