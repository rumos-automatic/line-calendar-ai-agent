# Technical Context (GCP版)

*2025年4月14日 更新: GCP移行と段階的NLP導入を反映*

## Technology Stack (GCP Based)

### Backend
- **Language:** Python 3.9+
- **Framework:** FastAPI
- **Runtime:** Google Cloud Run (via Docker)
- **Database:** Google Cloud Firestore
- **Async Tasks:** Google Cloud Tasks, Google Cloud Scheduler
- **Authentication:** Google OAuth 2.0 (PKCE), LINE Login
- **Secret Management:** Google Cloud Secret Manager
- **NLP (Initial):** Custom Pattern Matching (Keywords, Regex, Datetime Patterns)
- **NLP (Future):** OpenAI Agents SDK

### Frontend (LIFF)
- HTML, CSS, JavaScript
- (Optional) Frontend Framework like Vue.js, React

### External APIs/SDKs
- LINE Messaging API SDK (Python v3)
- LINE LIFF SDK (JavaScript)
- Google Calendar API v3 (google-api-python-client)
- Google Authentication Library (google-auth-oauthlib, google-cloud-secret-manager, google-cloud-firestore, google-cloud-tasks)

### Development Tools
- VS Code
- Git / GitHub
- Docker / Docker Compose
- Python Virtual Environment (`venv`, `conda`, etc.)
- `pip` (for dependency management via `requirements.txt`)
- `gcloud` CLI
- (Optional) `ngrok`

### Testing
- `pytest`
- `pytest-asyncio`
- `requests-mock` (for mocking external HTTP requests)
- `unittest.mock`
- Firestore Emulator
- (Optional) `pytest-cov` (for coverage)

### CI/CD & Deployment
- Docker
- GitHub Actions
- Google Cloud Build (implicitly used by Cloud Run deployment)
- Google Artifact Registry
- Google Cloud Run

## Dependencies (`requirements.txt` - Revised)

*注意: これはGCP移行後、初期リリース段階（パターン認識NLP）を想定した依存関係です。不要なライブラリ (SQLAlchemy, APScheduler, openai-agents) は削除されています。*

```txt
# Core Framework & Server
fastapi>=0.78.0 # Check latest stable version
uvicorn[standard]>=0.17.0 # Includes websockets, http-tools etc.

# LINE Integration
line-bot-sdk>=3.0.0

# Google Cloud Integration
google-cloud-firestore>=2.5.0
google-cloud-tasks>=2.7.0
google-cloud-scheduler>=2.3.0
google-cloud-secret-manager>=2.8.0
google-api-python-client>=2.30.0 # For Google Calendar API
google-auth-oauthlib>=0.5.0 # For OAuth flow
google-auth-httplib2>=0.1.0 # Required by google-api-python-client
google-auth>=2.6.0 # Core auth library

# Utilities
python-dotenv>=0.20.0 # For local .env file loading
pydantic>=1.9.0 # For data validation (FastAPI dependency)
pydantic-settings>=2.0.0 # For loading settings
pytz>=2022.1 # For timezone handling
cryptography>=36.0.0 # For token encryption
python-json-logger>=2.0.0 # For structured logging (optional but recommended)

# Add other necessary libraries for pattern matching NLP, etc.
# Example: regex library if needed beyond standard 're'
```

*開発用依存関係 (`requirements-dev.txt` などに分離推奨):*
```txt
pytest
pytest-asyncio
requests-mock
flake8
black
mypy
# Add other dev tools like coverage plugins etc.
```

## API Integration

### LINE Platform Integration
- **LINE Messaging API:**
    - Webhook endpoint on Cloud Run (`/webhook`).
    - Signature verification using Channel Secret (from Secret Manager).
    - Event handling (Message, Follow, Unfollow, Postback) using `line-bot-sdk`.
    - Sending Reply/Push messages using Channel Access Token (from Secret Manager).
- **LINE LIFF:**
    - LIFF App hosted (e.g., on Cloud Run static files or Cloud Storage).
    - Initiates Google OAuth flow via backend endpoint (`/liff/auth/google`).
    - Displays settings, authentication status fetched from backend API (`/liff/status`, `/liff/settings`).
    - Uses `liff.getProfile()` to get `line_user_id`.

### Google Cloud Integration
- **Google Calendar API:**
    - Authenticated using OAuth 2.0 Credentials obtained via LIFF flow (refreshed using stored encrypted refresh token).
    - CRUD operations for calendar events (`google-api-python-client`).
- **Firestore:**
    - Storing user data, preferences, encrypted refresh tokens.
    - Accessed via `google-cloud-firestore` library using Cloud Run service account credentials.
- **Secret Manager:**
    - Storing LINE/Google API secrets, encryption key.
    - Accessed via `google-cloud-secret-manager` library using Cloud Run service account credentials.
- **Cloud Tasks/Scheduler:**
    - Scheduling and queuing asynchronous tasks (reminders, token refresh).
    - Triggered by Cloud Scheduler, tasks added to Cloud Tasks queue targeting Cloud Run endpoints (`/tasks/...`).

### NLP Integration (Initial)
- Custom Python modules within the Cloud Run service (`nlp/`).
- Uses keywords, regex, and potentially libraries like `pytz` for datetime parsing.
- Called by the main service logic after receiving a message.

## Development Setup (GCP Based)

1.  **Prerequisites:** Install Python, Docker, gcloud CLI.
2.  **Clone Repository:** Get the project code.
3.  **Set up Python Virtual Environment:** Create and activate (e.g., `python -m venv venv && source venv/bin/activate`).
4.  **Install Dependencies:** `pip install -r requirements.txt` (and `requirements-dev.txt`).
5.  **GCP Authentication (Local):** Authenticate gcloud CLI for Application Default Credentials (`gcloud auth application-default login`). This allows local code to access GCP services like Secret Manager and Firestore (if not using emulators).
6.  **Configure Local Environment (`.env`):** Create a `.env` file (from `.env.example`) and set `GOOGLE_CLOUD_PROJECT` and potentially Firestore/Secret Manager emulator settings if used. **Do not put secrets in `.env`.**
7.  **(Recommended) Set up Docker Compose:** Configure `docker-compose.yml` to run the FastAPI app and Firestore emulator.
8.  **Run Locally:**
    *   Using Docker Compose: `docker-compose up --build`
    *   Directly (if not using Docker): `uvicorn src.main:app --reload --port 8000` (ensure necessary env vars are set).
9.  **(Optional) Run ngrok:** Expose the local server for LINE Webhook testing (`ngrok http 8000`).

## Code Organization (Revised)

```
src/
  ├── main.py         # FastAPI app entry point
  ├── core/           # Core components (config, logging, security)
  │   ├── config.py
  │   └── security.py # e.g., password hashing, token utils (if needed beyond OAuth)
  ├── routers/        # API endpoint definitions (FastAPI routers)
  │   ├── line_webhook.py
  │   ├── liff.py
  │   └── tasks.py
  ├── services/       # Business logic layer
  │   ├── line_service.py
  │   ├── google_calendar_service.py
  │   ├── auth_service.py
  │   ├── reminder_service.py
  │   └── message_handler.py # Orchestrates NLP and service calls
  ├── repositories/   # Data access layer (Firestore)
  │   ├── base_repository.py
  │   └── user_repository.py
  ├── models/         # Pydantic models for data validation & Firestore data classes
  │   ├── request.py
  │   ├── response.py
  │   └── firestore_models.py
  ├── nlp/            # Natural Language Processing (Initial: Pattern Matching)
  │   ├── parser.py
  │   └── datetime_patterns.py
  ├── utils/          # Utility functions
  ├── templates/      # HTML templates (for LIFF, if served by FastAPI)
  └── static/         # Static files (CSS, JS for LIFF)
tests/                # Pytest tests
  ├── integration/
  └── unit/
.github/              # GitHub Actions workflows
  └── workflows/
      └── deploy.yml
.env.example          # Example environment variables
.gitignore
Dockerfile            # For building the Cloud Run container
docker-compose.yml    # For local development environment (optional)
requirements.txt      # Production dependencies
requirements-dev.txt  # Development dependencies (optional)
README.md
# Other config files (logging.conf, etc.)
```

## Environment Variables & Secrets (GCP Context)

-   **Environment Variables (Set in Cloud Run):**
    -   `GOOGLE_CLOUD_PROJECT`: GCP Project ID.
    -   `ENVIRONMENT`: Deployment environment (`development`, `staging`, `production`).
    -   `LOG_LEVEL`: Logging level (e.g., `INFO`, `DEBUG`).
    -   References to Secret Manager secrets (e.g., `LINE_CHANNEL_SECRET_SM_REF=projects/PROJECT_ID/secrets/line-channel-secret/versions/latest`). Cloud Run automatically resolves these.
-   **Secrets (Stored in Secret Manager):**
    -   `line-channel-secret`
    -   `line-channel-access-token`
    -   `google-client-id`
    -   `google-client-secret`
    -   `google-redirect-uri`
    -   `google-refresh-token-encryption-key`
    -   `openai-api-key` (Future)

## Development Workflow (GCP Based)

1.  **Branch:** Create a feature branch from `main` or `develop`.
2.  **Develop Locally:** Use Docker Compose or run directly, leveraging GCP emulators or actual GCP services via ADC. Write code and unit tests.
3.  **Test Locally:** Run `pytest` within the virtual environment or Docker container.
4.  **Format & Lint:** Use `black` and `flake8`.
5.  **Push & Pull Request:** Push changes to GitHub and create a PR against `main` or `develop`.
6.  **CI:** GitHub Actions automatically runs linters, tests, vulnerability scans on the PR.
7.  **Code Review:** Team members review the PR.
8.  **Merge:** Merge the PR into `main` or `develop`.
9.  **CD:** GitHub Actions automatically builds the Docker image, pushes it to Artifact Registry, and deploys to Cloud Run (Staging first, then potentially Production after approval/further testing).
10. **Monitor:** Observe logs and metrics in Cloud Logging/Monitoring after deployment.
