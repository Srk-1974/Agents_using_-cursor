from agents.agent_linkedin import LINKEDIN_MAX_CHARACTERS, LinkedInPublisherAgent
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


def test_build_post_respects_linkedin_character_limit():
    agent = LinkedInPublisherAgent(_settings())
    very_long_topic = "A" * 6000
    guidance = {
        "headline": "H" * 6000,
        "tone": "professional",
        "cta": "Please engage.",
    }

    post = agent._build_post(very_long_topic, guidance)  # noqa: SLF001 - testing formatting contract.
    assert len(post) <= LINKEDIN_MAX_CHARACTERS
