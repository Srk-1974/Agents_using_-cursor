"""Application entrypoint."""

from agents.agent_linkedin import LinkedInPublisherAgent
from agents.agent_orchestrator import AgentOrchestrator
from agents.agent_youtube import YouTubeResearcherAgent
from config import Settings
from cursor_integration import CursorCoordinator
from gui_main import launch_app


def build_orchestrator() -> AgentOrchestrator:
    settings = Settings.from_env()
    linkedin_agent = LinkedInPublisherAgent(settings)
    youtube_agent = YouTubeResearcherAgent(settings)
    cursor_coordinator = CursorCoordinator(settings)
    return AgentOrchestrator(linkedin_agent, youtube_agent, cursor_coordinator)


if __name__ == "__main__":
    launch_app(build_orchestrator())
