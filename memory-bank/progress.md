# Project Progress (GCP Migration Phase)

*2025年4月14日 更新: GCP移行計画と段階的NLP導入方針を反映*

## Completed
- Initial project planning & architecture design (Pre-GCP)
- Initial Memory Bank setup
- Technology stack selection (Pre-GCP)
- **GCP Migration Planning & Documentation:**
    - Analysis of past development (`LESSONS_LEARNED.md`)
    - Revision of requirements for GCP & phased NLP (`カレンダーLINE連携要件定義.md`)
    - Design of GCP-based architecture (`SYSTEM_DESIGN_GCP.md`)
    - Creation of development/operational notes (`DEVELOPMENT_NOTES.md`)
    - Update of API implementation guides (`GoogleカレンダーAPI実装ガイド.txt`, `LINE連携 最新実装ガイド.txt`, `OpenAI agents SDK導入ガイド.txt`)
    - Update of project overview (`README.md`)
    - Update of Memory Bank files (`systemPatterns.md`, `techContext.md`, `activeContext.md`, `progress.md`)

## In Progress
- Preparation for GCP environment setup and initial implementation phase.

## Upcoming (Initial Release Focus)
1.  **Environment Setup:**
    -   Set up GCP project, enable APIs, configure IAM.
    -   Set up Secret Manager with necessary secrets.
    -   Configure LINE Developers Console (Webhook, LIFF).
    -   Configure Google Cloud Console (OAuth Client ID).
    -   Set up local development environment (Docker Compose, Firestore Emulator).
    -   Set up initial CI/CD pipeline (GitHub Actions for Lint, Test, Build, Push).
2.  **Core Feature Implementation:**
    -   Implement Google OAuth 2.0 (PKCE) flow via LIFF.
    -   Implement secure token storage (Firestore + Encryption).
    -   Implement LINE Webhook handler (FastAPI + BackgroundTasks).
    -   Implement basic pattern-based NLP engine (Intent parsing, Datetime extraction).
    -   Implement Google Calendar API integration (CRUD operations).
    -   Implement message processing logic connecting NLP and Calendar service.
    -   Implement Reminder system using Cloud Tasks & Scheduler.
3.  **Testing & Deployment:**
    -   Implement unit and integration tests (using emulators/mocks).
    -   Set up staging environment on Cloud Run via CI/CD.
    -   Perform E2E testing on staging.
    -   Deploy to production environment on Cloud Run.
    -   Set up monitoring and alerting (Cloud Logging/Monitoring).

## Known Issues
- Cloud Run environment variable loading behavior needs careful handling during implementation and testing (Ref: `LESSONS_LEARNED.md`).
- SDK/API version compatibility requires ongoing attention.

## Project Timeline (Revised - GCP Based)
- **Phase 1: Planning & Setup (Completed)** - GCP Migration Planning, Documentation, Initial Setup Prep.
- **Phase 2: Core Implementation (Current Focus)** - GCP Env Setup, CI/CD, Docker, Auth, Webhook, Basic NLP, Calendar CRUD, Reminders.
- **Phase 3: Testing & Staging Deployment** - Comprehensive Testing (Unit, Integration, E2E), Deployment to Staging.
- **Phase 4: Production Deployment & Monitoring** - Deployment to Production, Monitoring Setup, Initial Operation.
- **Phase 5: Post-Launch Iteration** - User Feedback Collection, Bug Fixing, Performance Tuning.
- **Phase 6: Advanced NLP (Future)** - OpenAI Agents SDK Integration.
- **Phase 7: Further Enhancements (Future)** - Advanced Calendar Features, etc.

## Technical Debt
- Reset to none at the beginning of this GCP migration phase. Need to be mindful not to introduce new debt by taking shortcuts.

## Decision Log (Updated)
1. Switched to Python (FastAPI) for backend.
2. **Adopted GCP as the cloud platform.**
3. **Chose Cloud Run for containerized application hosting.**
4. **Selected Firestore as the primary database.**
5. **Utilizing Cloud Tasks & Scheduler for async/scheduled jobs.**
6. **Using Secret Manager for sensitive data.**
7. Adopted LINE LIFF for seamless authentication and settings UI.
8. **Implementing Google OAuth 2.0 with PKCE flow.**
9. **Decided on a phased NLP approach: Pattern Matching first, OpenAI Agents SDK later.**
10. **Implementing CI/CD using GitHub Actions.**
11. **Using Docker for containerization and local development consistency.**
12. Adopted Memory Bank system for knowledge persistence.

## Milestones (Revised - GCP Based)
- [x] Project Initialization & Initial Planning (Pre-GCP)
- [x] GCP Migration Planning & Documentation Complete
- [ ] GCP Environment Setup Complete
- [ ] Local Development Environment (Docker Compose) Ready
- [ ] CI/CD Pipeline (Lint, Test, Build, Push) Operational
- [ ] Authentication Flow (LIFF + Google PKCE) Implemented
- [ ] LINE Webhook Handler Implemented
- [ ] Basic Pattern-Based NLP Engine Implemented
- [ ] Google Calendar CRUD Operations Implemented
- [ ] Reminder System (Cloud Tasks/Scheduler) Implemented
- [ ] Unit & Integration Test Coverage Achieved (Target: 80%+)
- [ ] Staging Environment Deployment Successful
- [ ] E2E Testing on Staging Complete
- [ ] Production Environment Deployment Successful
- [ ] Monitoring & Alerting Setup Complete
- [ ] (Future) OpenAI Agents SDK Integrated

## Notes
- Project is now focused on implementing the defined GCP-based architecture.
- Initial release will prioritize core functionality with pattern-based NLP.
- OpenAI Agents SDK integration is planned as a post-launch enhancement.
- Emphasis on CI/CD, automated testing, and robust monitoring from the start.
