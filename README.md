# Multi-Agent Desktop App (PyQt5)

Desktop GUI that runs three coordinated AI agents:

- Agent 1: LinkedIn Publisher
- Agent 2: YouTube Researcher
- Agent 3: Orchestrator (coordinates both and streams status updates)

For **step-by-step LinkedIn, YouTube, and `.env` setup**, see **[SETUP.md](SETUP.md)**.

## Project Structure

```text
Cusor_newproject/
├── agents/
│   ├── __init__.py
│   ├── agent_linkedin.py
│   ├── agent_orchestrator.py
│   └── agent_youtube.py
├── tests/
│   ├── test_linkedin_agent.py
│   ├── test_orchestrator.py
│   └── test_youtube_agent.py
├── .env.example
├── config.py
├── cursor_integration.py
├── gui_main.py
├── main.py
├── multi_agent_app.spec
├── README.md
├── SETUP.md
├── streamlit_app.py
└── requirements.txt
```

## 1) LinkedIn Developer App and OAuth 2.0 Setup

1. Open [LinkedIn Developer Portal](https://www.linkedin.com/developers/).
2. Create an app and attach it to your LinkedIn page/company where requested.
3. In your app:
   - Enable products/permissions needed for posting (typically `w_member_social`).
   - Configure an OAuth Redirect URL.
4. Perform OAuth 2.0 authorization:
   - Build authorization URL:
     - `https://www.linkedin.com/oauth/v2/authorization`
     - Query params: `response_type=code`, `client_id`, `redirect_uri`, `scope=w_member_social%20openid%20profile`.
   - Exchange `code` for token:
     - `POST https://www.linkedin.com/oauth/v2/accessToken`
     - Include `grant_type=authorization_code`, `code`, `redirect_uri`, `client_id`, `client_secret`.
5. Save resulting `access_token` in `.env` as `LINKEDIN_ACCESS_TOKEN`.
6. If your app returns a refresh token, set `LINKEDIN_REFRESH_TOKEN` too.

## 2) YouTube Data API v3 Setup

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project.
3. Enable **YouTube Data API v3** for the project.
4. Go to **APIs & Services -> Credentials**.
5. Create an API key.
6. Add this key to `.env` as `YOUTUBE_API_KEY`.

## 3) Install and Run

1. Create virtual environment:
   - Windows PowerShell:
     - `python -m venv .venv`
     - `.venv\Scripts\Activate.ps1`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Create `.env` from template:
   - `copy .env.example .env`
4. Fill in all required credentials in `.env`.
5. Launch app:
   - `python main.py`

## 4) GUI Behavior

- Enter a topic and click **Run Agents**.
- Status indicators update live:
  - `Idle -> Running -> Complete` or `Error`
- Output includes:
  - LinkedIn publish result (including post URL when available)
  - YouTube ranked research report (title, channel, views, summary, link)

## 5) Run Automated Tests

1. Activate your virtual environment.
2. Run:
   - `pytest -q`

The test suite covers:
- Orchestrator status/event flow
- LinkedIn content length enforcement
- YouTube result parsing and view-based ranking

## 6) Build Windows Executable (.exe)

1. Activate your virtual environment.
2. Build:
   - `pyinstaller multi_agent_app.spec`
3. Final app location:
   - `dist\multi_agent_app.exe`

Notes:
- Keep `.env` beside the executable so credentials are loaded at runtime.
- If SmartScreen prompts, sign the executable for production distribution.

## 7) Notes on Error Handling

The app handles common production errors with descriptive feedback:

- OAuth/auth failures (invalid or expired LinkedIn token)
- LinkedIn and YouTube HTTP/API errors
- YouTube quota/rate limit responses (`403` / `429`)
- Network timeouts and malformed API responses

## 8) Deploy as Public Website (Streamlit)

You can deploy the app as a public web UI using Streamlit.

1. Push this repo to GitHub (already done in your case).
2. Open [Streamlit Community Cloud](https://share.streamlit.io/) and connect your GitHub repo.
3. Select:
   - **Repository:** `Srk-1974/Agents_using_-cursor`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
4. In Streamlit app settings, add these secrets/env vars:
   - `LINKEDIN_CLIENT_ID`
   - `LINKEDIN_CLIENT_SECRET`
   - `LINKEDIN_ACCESS_TOKEN`
   - `LINKEDIN_REFRESH_TOKEN` (optional)
   - `YOUTUBE_API_KEY`
   - `REQUEST_TIMEOUT_SECONDS` (optional)
   - `CURSOR_API_KEY` and `CURSOR_API_BASE_URL` (optional)
5. Click deploy.

For local web run:

- `streamlit run streamlit_app.py`

## 9) Optional Cursor Integration

`cursor_integration.py` attempts to fetch structured post guidance from Cursor APIs when `CURSOR_API_KEY` is provided.

- If not configured or unavailable, it gracefully falls back to deterministic local guidance.
- This keeps the app fully runnable without Cursor credentials while still supporting Cursor-enhanced orchestration where available.
