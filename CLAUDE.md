# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 1. Common Development Commands

### Setup and Install
```bash
# Create Python virtual environment
python -m venv venv_py312  # Or similar name
source venv_py312/bin/activate  # Linux/macOS
# venv_py312\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development tools
```

### Local Development
```bash
# Run with Docker Compose (recommended)
docker-compose up -d --build

# Run FastAPI directly
uvicorn src.main:app --reload --port 8000

# Expose local server for LINE webhook testing
ngrok http 8000
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/unit/test_nlp.py
```

### Code Quality
```bash
# Format code
black src tests

# Check formatting
black --check src tests

# Lint code
flake8 src tests

# Type checking
mypy src
```

### Build and Deploy
```bash
# Build Docker image
docker build -t line-calendar-agent .

# The deployment is automated via GitHub Actions when merging to main branch
# Manual deployment requires gcloud CLI setup
```

## 2. High-Level Architecture

This is a Google Cloud Platform (GCP) based LINE-Google Calendar integration system with the following architecture:

### Core Services (GCP)
- **Cloud Run**: Hosts the FastAPI application in a containerized, serverless environment
- **Firestore**: NoSQL database for user data, preferences, and encrypted tokens
- **Secret Manager**: Stores API keys, OAuth secrets, and encryption keys
- **Cloud Tasks/Scheduler**: Handles asynchronous operations and scheduled reminders

### Application Architecture
- **FastAPI Backend**: Main application server handling webhooks, authentication, and business logic
- **LINE Integration**: 
  - Webhook endpoint for receiving messages
  - LIFF application for OAuth flow and settings
- **Google Calendar Integration**: CRUD operations via Google Calendar API
- **NLP Processing**: 
  - Initial: Pattern-based matching for Japanese datetime expressions
  - Future: OpenAI Agents SDK for advanced language understanding

### Authentication Flow
- Uses LINE LIFF for seamless in-app authentication
- Implements Google OAuth 2.0 with PKCE for enhanced security
- Encrypted refresh token storage in Firestore

### Key Design Decisions
1. **Phased NLP Approach**: Starting with pattern matching, planning to integrate OpenAI Agents SDK post-launch
2. **Serverless Architecture**: Leveraging GCP managed services for scalability and reduced operational overhead
3. **Security First**: All secrets in Secret Manager, encrypted token storage, PKCE OAuth flow
4. **CI/CD Pipeline**: GitHub Actions for automated testing, building, and deployment

### Directory Structure
```
src/
  ├── main.py           # FastAPI app entry point
  ├── core/             # Config, logging, security utilities
  ├── routers/          # API endpoints (webhook, LIFF, tasks)
  ├── services/         # Business logic layer
  ├── repositories/     # Firestore data access layer
  ├── models/           # Pydantic models and data structures
  ├── nlp/              # Natural language processing
  └── utils/            # Helper functions
```

### Important Considerations
- Always verify environment variables are properly set in Cloud Run
- Use Secret Manager references for sensitive data, never hardcode
- Implement proper error handling and structured logging for Cloud Logging
- Follow the Repository pattern for Firestore operations
- Ensure webhook responses are within LINE's timeout limits (use background tasks)