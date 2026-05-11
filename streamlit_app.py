"""Streamlit web UI for the multi-agent workflow."""

from __future__ import annotations

from typing import Dict, List, Tuple

import streamlit as st

from agents.agent_linkedin import LinkedInPublisherAgent
from agents.agent_orchestrator import AgentOrchestrator
from agents.agent_youtube import YouTubeResearcherAgent
from config import Settings
from cursor_integration import CursorCoordinator


STATUS_ICONS = {
    "Idle": "⚪",
    "Running": "🟡",
    "Complete": "🟢",
    "Error": "🔴",
}


def build_orchestrator() -> AgentOrchestrator:
    settings = Settings.from_env()
    return AgentOrchestrator(
        linkedin_agent=LinkedInPublisherAgent(settings),
        youtube_agent=YouTubeResearcherAgent(settings),
        cursor_coordinator=CursorCoordinator(settings),
    )


def default_status() -> Dict[str, Tuple[str, str]]:
    return {
        "linkedin": ("Idle", "Waiting"),
        "youtube": ("Idle", "Waiting"),
        "orchestrator": ("Idle", "Waiting"),
    }


def draw_status_cards(status_map: Dict[str, Tuple[str, str]]) -> None:
    col1, col2, col3 = st.columns(3)
    for col, key, title in (
        (col1, "linkedin", "Agent 1 - LinkedIn Publisher"),
        (col2, "youtube", "Agent 2 - YouTube Researcher"),
        (col3, "orchestrator", "Agent 3 - Orchestrator"),
    ):
        status, message = status_map[key]
        icon = STATUS_ICONS.get(status, "⚪")
        col.markdown(f"**{title}**")
        col.info(f"{icon} {status} - {message}")


def render_results(result: dict) -> None:
    linkedin = result.get("linkedin")
    youtube = result.get("youtube")

    st.subheader("LinkedIn Result")
    if linkedin:
        st.write(f"**Success:** {linkedin.success}")
        st.write(f"**Message:** {linkedin.message}")
        if linkedin.post_url:
            st.write(f"**Post URL:** {linkedin.post_url}")
        st.text_area("Generated Post Content", linkedin.content, height=190)
    else:
        st.warning("No LinkedIn result available.")

    st.subheader("YouTube Research Report")
    if youtube and youtube.videos:
        st.write(f"**Message:** {youtube.message}")
        for idx, video in enumerate(youtube.videos, start=1):
            with st.expander(f"{idx}. {video.title}", expanded=idx <= 3):
                st.write(f"**Channel:** {video.channel}")
                st.write(f"**Views:** {video.views:,}")
                st.write(f"**URL:** {video.url}")
                summary = (video.description[:320] + "...") if len(video.description) > 320 else video.description
                st.write(f"**Summary:** {summary}")
    elif youtube:
        st.warning(youtube.message)
    else:
        st.warning("No YouTube result available.")

    if result.get("errors"):
        st.subheader("Errors")
        for error in result["errors"]:
            st.error(error)


def main() -> None:
    st.set_page_config(page_title="Multi-Agent AI Workflow", page_icon="🤖", layout="wide")
    st.title("Multi-Agent AI Workflow Studio")
    st.caption("Run LinkedIn publishing and YouTube research in one coordinated workflow.")

    if "status_map" not in st.session_state:
        st.session_state.status_map = default_status()
    if "status_history" not in st.session_state:
        st.session_state.status_history: List[Tuple[str, str, str]] = []
    if "last_result" not in st.session_state:
        st.session_state.last_result = None

    topic = st.text_input("Topic", placeholder="Artificial intelligence")
    draw_status_cards(st.session_state.status_map)
    status_log = st.empty()
    if st.session_state.status_history:
        status_log.code(
            "\n".join(
                [f"[{agent}] {status}: {message}" for agent, status, message in st.session_state.status_history[-12:]]
            )
        )

    if st.button("Run Agents", type="primary"):
        if not topic.strip():
            st.warning("Please enter a topic before running agents.")
            return

        st.session_state.status_map = default_status()
        st.session_state.status_history = []
        orchestrator = build_orchestrator()

        def status_callback(agent_name: str, status: str, message: str) -> None:
            st.session_state.status_map[agent_name] = (status, message)
            st.session_state.status_history.append((agent_name, status, message))
            status_log.code(
                "\n".join(
                    [
                        f"[{agent}] {state}: {msg}"
                        for agent, state, msg in st.session_state.status_history[-12:]
                    ]
                )
            )

        with st.spinner("Running agents..."):
            result = orchestrator.run(topic=topic, status_callback=status_callback)
        st.session_state.last_result = result
        st.success("Workflow completed.")

    if st.session_state.last_result:
        render_results(st.session_state.last_result)


if __name__ == "__main__":
    main()
