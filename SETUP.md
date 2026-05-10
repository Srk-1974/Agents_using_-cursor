# Credentials setup guide

This document walks through obtaining **LinkedIn** OAuth client credentials and access tokens, a **YouTube Data API v3** key, and optional **Cursor** settings for this desktop app. Values go in a `.env` file next to `main.py` (see `.env.example`).

---

## Part A — LinkedIn (Client ID, Client Secret, Access Token)

### A1. Create a LinkedIn Developer application

1. Open the [LinkedIn Developers](https://www.linkedin.com/developers/) portal and sign in.
2. Click **Create app** (or open an existing app).
3. Fill in the required fields (app name, LinkedIn Page association if asked, legal agreement).
4. After the app exists, open it from **My apps**.

You will use this app for OAuth and for API calls that post on behalf of a **member** (your account), subject to LinkedIn product access and approval rules.

### A2. Note Client ID and Client Secret

1. In your app, open the **Auth** (or **Authentication**) section.
2. Copy:
   - **Client ID** → use as `LINKEDIN_CLIENT_ID` in `.env`.
   - **Client Secret** → use as `LINKEDIN_CLIENT_SECRET` in `.env`.

Keep the client secret private. Do not commit `.env` to Git (use `.env.example` only as a template).

### A3. Configure OAuth 2.0 redirect URL

1. Still under **Auth**, find **OAuth 2.0 settings** / **Authorized redirect URLs for your app**.
2. Add a redirect URL you control. For local manual testing, a common pattern is:

   `http://localhost:8080/callback`

   (You can use another path or port; it must **exactly** match what you use in the authorization URL and token exchange in the next steps.)

3. Save changes.

### A4. Request the right API access (products / scopes)

LinkedIn ties many capabilities to **products** and **OAuth scopes**. For posting as a member, apps typically need access aligned with **Share on LinkedIn** / member posting capabilities and related scopes (LinkedIn’s UI and naming can change; follow the portal for your app).

Scopes this project’s README references as an example include:

- `openid`, `profile` — identity / profile (often used with “Sign In with LinkedIn” style flows).
- `w_member_social` — **create member posts** (when your app is approved for that product).

**What you must do in the portal:** enable the product(s) that grant **UGC posting** for members, and ensure your OAuth request uses scopes that match what the product allows. If a scope is not available, your app may need **verification** or a different product tier—follow LinkedIn’s onboarding in the developer UI.

### A5. Run the OAuth authorization step (get an authorization `code`)

Build an authorization URL (replace placeholders with your values):

```text
https://www.linkedin.com/oauth/v2/authorization
  ?response_type=code
  &client_id=YOUR_CLIENT_ID
  &redirect_uri=YOUR_URL_ENCODED_REDIRECT
  &scope=SPACE_SEPARATED_SCOPES_URL_ENCODED
```

Example scopes string (space-separated, then URL-encoded): `openid profile w_member_social`.

Steps:

1. Paste the full URL into a browser.
2. Approve consent when prompted.
3. After redirect, copy the `code` query parameter from the browser address bar (before it expires).

### A6. Exchange the `code` for tokens

Send a **POST** request to LinkedIn’s token endpoint (you can use Postman, Insomnia, or `curl`):

- **URL:** `https://www.linkedin.com/oauth/v2/accessToken`
- **Content-Type:** `application/x-www-form-urlencoded`
- **Body fields** (typical authorization-code flow):

  | Field           | Value |
  |-----------------|--------|
  | `grant_type`    | `authorization_code` |
  | `code`          | the `code` from the redirect |
  | `redirect_uri`  | same redirect URI as in A3 (must match exactly) |
  | `client_id`     | your Client ID |
  | `client_secret` | your Client Secret |

From the JSON response, copy:

- **access_token** → `LINKEDIN_ACCESS_TOKEN` in `.env`.
- **refresh_token** (if present) → `LINKEDIN_REFRESH_TOKEN` in `.env`.

Access tokens expire. If you obtain a refresh token and keep `LINKEDIN_CLIENT_ID` / `LINKEDIN_CLIENT_SECRET` in `.env`, this app’s LinkedIn agent can attempt a refresh when the access token is rejected (see `agents/agent_linkedin.py`).

### A7. Verify the member can post (expectations)

- The token must be a **member** token with permission to call the UGC Post API for your use case.
- If LinkedIn returns **403** or **product not available**, resolve product/scopes/verification in the LinkedIn developer portal rather than changing this repo alone.

---

## Part B — YouTube Data API v3 (API key)

### B1. Google Cloud project

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Create a **new project** or select an existing one.

### B2. Enable YouTube Data API v3

1. Go to **APIs & Services** → **Library** (or search “APIs & Services”).
2. Search for **YouTube Data API v3**.
3. Open it and click **Enable**.

### B3. Create an API key

1. Go to **APIs & Services** → **Credentials**.
2. Click **Create credentials** → **API key**.
3. Copy the key → use as `YOUTUBE_API_KEY` in `.env`.

### B4. Restrict the key (recommended)

1. Edit the key under **API restrictions**: restrict to **YouTube Data API v3**.
2. Under **Application restrictions**, choose what fits your use case (for a server-style script on your PC, “None” is common for dev; IP or other restrictions apply more to deployed servers).

### B5. Quotas and billing

- YouTube Data API has a **daily quota** (default is often 10,000 units per day; search/list/video calls consume units). If you hit limits, the app may show quota-related errors. See [YouTube Data API overview](https://developers.google.com/youtube/v3/getting-started) for quota details.

---

## Part C — Optional Cursor integration

This app can call Cursor-style HTTP helpers when configured (`cursor_integration.py`).

1. If you use it, set in `.env`:
   - `CURSOR_API_KEY` — your API key, if applicable.
   - `CURSOR_API_BASE_URL` — base URL for your Cursor-compatible API (default in `.env.example` is a placeholder).
2. If these are empty, the app uses **local fallback** guidance and still runs.

---

## Part D — Wire everything into `.env`

1. In the project folder, copy the template:

   ```powershell
   copy .env.example .env
   ```

2. Edit `.env` and set at minimum:

   | Variable | Source |
   |----------|--------|
   | `LINKEDIN_CLIENT_ID` | LinkedIn app **Client ID** |
   | `LINKEDIN_CLIENT_SECRET` | LinkedIn app **Client Secret** |
   | `LINKEDIN_ACCESS_TOKEN` | OAuth **access_token** |
   | `LINKEDIN_REFRESH_TOKEN` | OAuth **refresh_token** if returned |
   | `YOUTUBE_API_KEY` | Google **API key** |

3. Optional: `REQUEST_TIMEOUT_SECONDS` (default `20`).

4. Save the file. **Restart** the application after any change to `.env`.

5. Run:

   ```powershell
   python main.py
   ```

---

## Part E — Troubleshooting checklist

| Symptom | What to check |
|--------|----------------|
| “Missing LinkedIn configuration” | All three of `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_ACCESS_TOKEN` are set in `.env`, no stray spaces, file is beside `main.py`. |
| “Missing YouTube configuration” | `YOUTUBE_API_KEY` set; API enabled on the same GCP project that owns the key. |
| LinkedIn 401 / invalid token | Token expired; redo OAuth or use refresh token + client id/secret. |
| LinkedIn 403 / insufficient permissions | Product or scopes not approved; fix in LinkedIn Developer Portal. |
| YouTube 403 quota | Daily quota exceeded or API key restrictions block the call. |
| Changes ignored | Restart the app; `.env` is read at startup. |

---

## Official references

- LinkedIn OAuth 2.0: [LinkedIn OAuth documentation](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authentication)
- YouTube Data API: [YouTube Data API documentation](https://developers.google.com/youtube/v3)
