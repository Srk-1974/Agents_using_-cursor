"""Streamlit web UI for the multi-agent workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import streamlit as st
from dotenv import set_key

from agents.agent_linkedin import LinkedInPublisherAgent
from agents.agent_orchestrator import AgentOrchestrator
from agents.agent_youtube import YouTubeResearcherAgent
from config import Settings
from cursor_integration import CursorCoordinator

ENV_FILE = Path(__file__).resolve().parent / ".env"


STATUS_ICONS = {
    "Idle": "⚪",
    "Running": "🟡",
    "Complete": "🟢",
    "Error": "🔴",
}


def build_orchestrator(settings: Settings) -> AgentOrchestrator:
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


def settings_to_form_values(settings: Settings) -> Dict[str, str]:
    return {
        "linkedin_client_id": settings.linkedin_client_id,
        "linkedin_client_secret": settings.linkedin_client_secret,
        "linkedin_access_token": settings.linkedin_access_token,
        "linkedin_refresh_token": settings.linkedin_refresh_token,
        "youtube_api_key": settings.youtube_api_key,
        "request_timeout_seconds": str(settings.request_timeout_seconds),
        "cursor_api_key": settings.cursor_api_key,
        "cursor_api_base_url": settings.cursor_api_base_url,
    }


def build_settings_from_form(form_values: Dict[str, str]) -> Settings:
    timeout_value = form_values.get("request_timeout_seconds", "20").strip() or "20"
    try:
        timeout = int(timeout_value)
    except ValueError:
        timeout = 20

    return Settings(
        linkedin_client_id=form_values.get("linkedin_client_id", "").strip(),
        linkedin_client_secret=form_values.get("linkedin_client_secret", "").strip(),
        linkedin_access_token=form_values.get("linkedin_access_token", "").strip(),
        linkedin_refresh_token=form_values.get("linkedin_refresh_token", "").strip(),
        youtube_api_key=form_values.get("youtube_api_key", "").strip(),
        request_timeout_seconds=timeout,
        cursor_api_key=form_values.get("cursor_api_key", "").strip(),
        cursor_api_base_url=form_values.get("cursor_api_base_url", "https://api.cursor.com").strip()
        or "https://api.cursor.com",
    )


def save_form_values_to_env(form_values: Dict[str, str]) -> None:
    ENV_FILE.touch(exist_ok=True)
    for key, value in (
        ("LINKEDIN_CLIENT_ID", form_values["linkedin_client_id"]),
        ("LINKEDIN_CLIENT_SECRET", form_values["linkedin_client_secret"]),
        ("LINKEDIN_ACCESS_TOKEN", form_values["linkedin_access_token"]),
        ("LINKEDIN_REFRESH_TOKEN", form_values["linkedin_refresh_token"]),
        ("YOUTUBE_API_KEY", form_values["youtube_api_key"]),
        ("REQUEST_TIMEOUT_SECONDS", form_values["request_timeout_seconds"]),
        ("CURSOR_API_KEY", form_values["cursor_api_key"]),
        ("CURSOR_API_BASE_URL", form_values["cursor_api_base_url"]),
    ):
        set_key(str(ENV_FILE), key, value)


def render_config_sidebar() -> Settings:
    st.sidebar.header("Configuration")
    st.sidebar.caption("Set API credentials in the GUI. Save to .env is for local machine runs only.")

    if "config_values" not in st.session_state:
        st.session_state.config_values = settings_to_form_values(Settings.from_env())

    config_values = st.session_state.config_values

    with st.sidebar.form("config_form", clear_on_submit=False):
        linkedin_client_id = st.text_input("LinkedIn Client ID", value=config_values["linkedin_client_id"])
        linkedin_client_secret = st.text_input(
            "LinkedIn Client Secret",
            value=config_values["linkedin_client_secret"],
            type="password",
        )
        linkedin_access_token = st.text_input(
            "LinkedIn Access Token",
            value=config_values["linkedin_access_token"],
            type="password",
        )
        linkedin_refresh_token = st.text_input(
            "LinkedIn Refresh Token (optional)",
            value=config_values["linkedin_refresh_token"],
            type="password",
        )
        youtube_api_key = st.text_input("YouTube API Key", value=config_values["youtube_api_key"], type="password")
        request_timeout_seconds = st.text_input(
            "Request Timeout (seconds)",
            value=config_values["request_timeout_seconds"],
        )
        cursor_api_key = st.text_input("Cursor API Key (optional)", value=config_values["cursor_api_key"], type="password")
        cursor_api_base_url = st.text_input(
            "Cursor API Base URL",
            value=config_values["cursor_api_base_url"] or "https://api.cursor.com",
        )

        apply_changes = st.form_submit_button("Apply in this session", type="primary")
        save_changes = st.form_submit_button("Save to .env (local machine only)")

    updated_values = {
        "linkedin_client_id": linkedin_client_id,
        "linkedin_client_secret": linkedin_client_secret,
        "linkedin_access_token": linkedin_access_token,
        "linkedin_refresh_token": linkedin_refresh_token,
        "youtube_api_key": youtube_api_key,
        "request_timeout_seconds": request_timeout_seconds,
        "cursor_api_key": cursor_api_key,
        "cursor_api_base_url": cursor_api_base_url,
    }

    if apply_changes or save_changes:
        st.session_state.config_values = updated_values
        st.sidebar.success("Configuration applied for this session.")

    if save_changes:
        try:
            save_form_values_to_env(updated_values)
            st.sidebar.success(f"Saved configuration to {ENV_FILE.name}.")
        except OSError as error:
            st.sidebar.error(f"Unable to save .env: {error}")

    return build_settings_from_form(st.session_state.config_values)


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
    active_settings = render_config_sidebar()

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
        orchestrator = build_orchestrator(active_settings)

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
