"""Orchestrator agent that coordinates all workflows."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict

from cursor_integration import CursorCoordinator

from .agent_linkedin import LinkedInPublisherAgent
from .agent_youtube import YouTubeResearcherAgent


StatusCallback = Callable[[str, str, str], None]


class AgentOrchestrator:
    def __init__(
        self,
        linkedin_agent: LinkedInPublisherAgent,
        youtube_agent: YouTubeResearcherAgent,
        cursor_coordinator: CursorCoordinator,
    ):
        self.linkedin_agent = linkedin_agent
        self.youtube_agent = youtube_agent
        self.cursor_coordinator = cursor_coordinator

    def run(self, topic: str, status_callback: StatusCallback) -> Dict[str, Any]:
        if not topic.strip():
            raise ValueError("Topic is required.")

        status_callback("orchestrator", "Running", "Preparing shared workflow context...")
        guidance = self.cursor_coordinator.build_linkedin_guidance(topic)

        status_callback("linkedin", "Running", "Publishing to LinkedIn...")
        status_callback("youtube", "Running", "Researching YouTube videos...")

        results: Dict[str, Any] = {"linkedin": None, "youtube": None}
        errors = []

        # Run both domain agents concurrently while the GUI remains responsive.
        with ThreadPoolExecutor(max_workers=2) as pool:
            future_map = {
                pool.submit(self.linkedin_agent.publish_post, topic, guidance): "linkedin",
                pool.submit(self.youtube_agent.research, topic): "youtube",
            }
            for future in as_completed(future_map):
                agent_name = future_map[future]
                try:
                    result = future.result()
                    results[agent_name] = result
                    is_success = bool(getattr(result, "success", False))
                    message = str(getattr(result, "message", "Completed"))
                    status_callback(agent_name, "Complete" if is_success else "Error", message)
                    if not is_success:
                        errors.append(f"{agent_name}: {message}")
                except Exception as error:  # noqa: BLE001 - UI should receive all failures.
                    errors.append(f"{agent_name}: {error}")
                    status_callback(agent_name, "Error", str(error))

        orchestrator_status = "Error" if errors else "Complete"
        orchestrator_message = "Finished with errors." if errors else "All agents completed successfully."
        status_callback("orchestrator", orchestrator_status, orchestrator_message)

        return {
            "topic": topic,
            "guidance": guidance,
            "linkedin": results["linkedin"],
            "youtube": results["youtube"],
            "errors": errors,
        }
