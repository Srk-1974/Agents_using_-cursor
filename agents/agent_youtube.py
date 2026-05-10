"""YouTube research agent implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import requests

from config import Settings


@dataclass
class VideoInsight:
    title: str
    channel: str
    views: int
    description: str
    url: str


@dataclass
class YouTubeResult:
    success: bool
    message: str
    videos: List[VideoInsight]


class YouTubeResearcherAgent:
    def __init__(self, settings: Settings):
        self.settings = settings

    def research(self, topic: str, max_results: int = 8) -> YouTubeResult:
        self.settings.validate_for_youtube()

        try:
            search_items = self._search(topic, max_results)
            if not search_items:
                return YouTubeResult(success=True, message="No YouTube videos found.", videos=[])

            video_ids = [item["id"]["videoId"] for item in search_items if item.get("id", {}).get("videoId")]
            detailed_videos = self._get_video_details(video_ids)
            return YouTubeResult(success=True, message="YouTube research complete.", videos=detailed_videos)
        except requests.HTTPError as http_error:
            status = http_error.response.status_code if http_error.response is not None else "unknown"
            if status == 403:
                msg = "YouTube API quota exceeded or key lacks permissions."
            elif status == 429:
                msg = "YouTube API rate limit reached."
            else:
                msg = f"YouTube HTTP error ({status})."
            return YouTubeResult(success=False, message=msg, videos=[])
        except (requests.RequestException, KeyError, ValueError, TypeError) as error:
            return YouTubeResult(success=False, message=f"YouTube research failed: {error}", videos=[])

    def _search(self, topic: str, max_results: int) -> List[Dict]:
        response = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "q": topic,
                "maxResults": max_results,
                "type": "video",
                "order": "relevance",
                "key": self.settings.youtube_api_key,
            },
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("items", [])

    def _get_video_details(self, video_ids: List[str]) -> List[VideoInsight]:
        response = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={
                "part": "snippet,statistics",
                "id": ",".join(video_ids),
                "key": self.settings.youtube_api_key,
            },
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()

        videos: List[VideoInsight] = []
        for item in payload.get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            video_id = item.get("id", "")
            videos.append(
                VideoInsight(
                    title=str(snippet.get("title", "Untitled")),
                    channel=str(snippet.get("channelTitle", "Unknown Channel")),
                    views=int(stats.get("viewCount", 0)),
                    description=str(snippet.get("description", "")).strip(),
                    url=f"https://www.youtube.com/watch?v={video_id}",
                )
            )
        # Rank by views so "high-performing" videos rise to the top.
        videos.sort(key=lambda item: item.views, reverse=True)
        return videos
