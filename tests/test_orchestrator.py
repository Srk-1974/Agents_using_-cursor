from config import Settings
from cursor_integration import CursorCoordinator
from agents.agent_linkedin import LinkedInResult
from agents.agent_orchestrator import AgentOrchestrator
from agents.agent_youtube import YouTubeResult


class FakeLinkedInAgent:
    def publish_post(self, topic, guidance):
        return LinkedInResult(
            success=True,
            message=f"Published about {topic}",
            post_url="https://linkedin.com/feed/update/fake",
            content=f"{guidance['headline']}\n{topic}",
        )


class FakeYouTubeAgent:
    def research(self, topic, max_results=8):
        return YouTubeResult(success=True, message=f"Research complete for {topic}", videos=[])


def test_orchestrator_runs_both_agents_and_reports_completion():
    settings = Settings(
        linkedin_client_id="id",
        linkedin_client_secret="secret",
        linkedin_access_token="token",
        linkedin_refresh_token="",
        youtube_api_key="key",
        request_timeout_seconds=5,
        cursor_api_key="",
        cursor_api_base_url="https://api.cursor.com",
    )
    orchestrator = AgentOrchestrator(
        linkedin_agent=FakeLinkedInAgent(),
        youtube_agent=FakeYouTubeAgent(),
        cursor_coordinator=CursorCoordinator(settings),
    )
    events = []

    def status_callback(agent_name, status, message):
        events.append((agent_name, status, message))

    result = orchestrator.run("AI automation", status_callback)

    assert result["linkedin"].success is True
    assert result["youtube"].success is True
    assert result["errors"] == []
    assert any(event[0] == "orchestrator" and event[1] == "Complete" for event in events)
