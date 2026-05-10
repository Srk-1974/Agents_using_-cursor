from unittest.mock import Mock, patch

from agents.agent_youtube import YouTubeResearcherAgent
from config import Settings


def _settings():
    return Settings(
        linkedin_client_id="id",
        linkedin_client_secret="secret",
        linkedin_access_token="token",
        linkedin_refresh_token="",
        youtube_api_key="key",
        request_timeout_seconds=5,
        cursor_api_key="",
        cursor_api_base_url="https://api.cursor.com",
    )


@patch("agents.agent_youtube.requests.get")
def test_youtube_research_sorts_by_view_count(mock_get: Mock):
    search_response = Mock()
    search_response.raise_for_status.return_value = None
    search_response.json.return_value = {
        "items": [
            {"id": {"videoId": "vid1"}},
            {"id": {"videoId": "vid2"}},
        ]
    }

    details_response = Mock()
    details_response.raise_for_status.return_value = None
    details_response.json.return_value = {
        "items": [
            {
                "id": "vid1",
                "snippet": {"title": "One", "channelTitle": "C1", "description": "Desc1"},
                "statistics": {"viewCount": "10"},
            },
            {
                "id": "vid2",
                "snippet": {"title": "Two", "channelTitle": "C2", "description": "Desc2"},
                "statistics": {"viewCount": "100"},
            },
        ]
    }
    mock_get.side_effect = [search_response, details_response]

    result = YouTubeResearcherAgent(_settings()).research("python")

    assert result.success is True
    assert len(result.videos) == 2
    assert result.videos[0].title == "Two"
    assert result.videos[0].views == 100
