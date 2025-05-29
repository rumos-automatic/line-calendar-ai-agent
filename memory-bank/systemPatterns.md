# System Patterns (GCP版)

*2025年4月14日 更新: GCP移行と段階的NLP導入を反映*

## 1. Architecture Overview (GCP Based)

GCPのマネージドサービスを活用したサーバーレスアーキテクチャを採用します。

```mermaid
graph TD
    subgraph User Interaction
        User[LINE User] --> LINE_Platform[LINE Platform]
    end

    subgraph GCP Infrastructure
        LINE_Platform -- Webhook --> CloudRun[Cloud Run Service (FastAPI)]
        LINE_Platform -- LIFF Request --> CloudRun
        CloudRun -- CRUD Ops --> Firestore[Firestore (Database)]
        CloudRun -- Read/Write Secrets --> SecretManager[Secret Manager]
        CloudRun -- Process Text --> NLPEngine[Pattern-Based NLP Engine (Initial)]
        NLPEngine -- Extract Info --> CloudRun
        CloudRun -- Schedule Task --> CloudTasks[Cloud Tasks]
        CloudScheduler[Cloud Scheduler] -- Trigger Task --> CloudTasks
        CloudTasks -- Execute Task --> CloudRun
        CloudRun -- Read/Write Events --> GoogleCalendar[Google Calendar API]
        CloudRun -- Log Events --> CloudLogging[Cloud Logging]
        CloudMonitoring[Cloud Monitoring] -- Monitor --> CloudRun & Other Services
        GitHubActions[GitHub Actions (CI/CD)] -- Deploy --> CloudRun
        GitHubActions -- Push Image --> ArtifactRegistry[Artifact Registry]
        subgraph Future Expansion
           CloudRun -- Call Agent --> OpenAIAgents[OpenAI Agents SDK]
        end
    end

    subgraph External Services
        GoogleCalendar -- API Call --> Google_API[Google APIs]
        OpenAIAgents -- API Call --> OpenAI_API[OpenAI API]
    end

    User -- Use LIFF --> LIFFApp[LIFF Application (Hosted on Cloud Run/Static)]
    LIFFApp -- Auth Request --> CloudRun
    LIFFApp -- Google Auth --> GoogleSignIn[Google Sign-In]
    GoogleSignIn -- Return Auth Code --> LIFFApp
```

### Core Components (GCP Services)

1.  **Cloud Run Service (Backend - FastAPI/Python):**
    *   ステートレスなコンテナ実行環境。
    *   LINE Webhook、LIFF API、非同期タスク処理のエンドポイントを提供。
    *   ビジネスロジック、NLP処理（初期）、外部API連携を担当。
    *   自動スケーリング（ゼロスケールも可能）。
2.  **Firestore (Database):**
    *   NoSQLドキュメントデータベース。
    *   ユーザー情報、設定、暗号化されたトークン、リマインダー状態などを格納。
    *   スケーラブルでサーバーレス環境に適している。
3.  **Secret Manager:**
    *   APIキー、OAuthクライアントシークレット、トークン暗号化キーなどの機密情報を安全に保管・管理。
    *   IAMによるアクセス制御。
4.  **NLP Engine (Initial Release):**
    *   Cloud Runサービス内で実装されるパターン認識（キーワード、正規表現、日時パターン）ベースの自然言語処理エンジン。
    *   ユーザーメッセージから意図と情報を抽出。
5.  **(Future) OpenAI Agents SDK:**
    *   リリース後の機能拡張で導入予定。
    *   より高度なNLP、ツール連携、会話管理を提供。NLP Engineを代替または連携。
6.  **Cloud Tasks & Cloud Scheduler (Notification/Async Manager):**
    *   Cloud Scheduler: 定期的なタスク（リマインダー生成、トークン更新チェック）をトリガー。
    *   Cloud Tasks: 非同期タスク（リマインダー送信、トークン更新実行）をキューイングし、Cloud Runのエンドポイントを呼び出して実行。信頼性の高いタスク実行とリトライを提供。
7.  **LIFF Application (Frontend):**
    *   LINE内で動作するWebアプリ (HTML/CSS/JS)。
    *   Google OAuth認証フローの開始、設定画面の提供。
    *   Cloud Run上で静的ファイルとしてホスト、またはCloud Storage + CDN等を利用。
8.  **Other GCP Services:**
    *   **Artifact Registry:** Dockerイメージの保存場所。
    *   **Cloud Logging & Monitoring:** ログ収集、監視、アラート。
    *   **GitHub Actions (CI/CD):** ビルド、テスト、デプロイの自動化パイプライン。

## 2. Design Patterns

GCPのマネージドサービスを活用しつつ、アプリケーション内部では以下のパターンを適用します。

-   **Repository Pattern:** Firestoreへのデータアクセスを抽象化し、ビジネスロジックからデータ永続化の詳細を分離します (`repositories/`)。
-   **Service Layer Pattern:** ビジネスロジックをカプセル化し、コントローラー (ルーター) とリポジトリの中間に配置します (`services/`)。
-   **Dependency Injection:** FastAPIの機能を活用し、DBセッション、サービス、リポジトリなどをエンドポイント関数に注入します。テスト容易性を向上させます。
-   **Strategy Pattern (for NLP):** 初期リリースでは、異なる種類の自然言語入力（予定追加、確認など）や日時表現を処理するための戦略（パーサー）を切り替え可能にします (`nlp/`)。将来的にAgents SDKに置き換える際のインターフェースとしても機能します。
-   **Asynchronous Task Queue (Cloud Tasks):** 時間のかかる処理や外部APIへの通知（LINEへのリマインダー送信）をバックグラウンドで実行し、Webhookの応答性を高めます。
-   **Scheduled Jobs (Cloud Scheduler):** 定期的な処理（毎日のリマインダー生成、トークン有効期限チェック）を自動実行します。

## 3. Data Flow

### Authentication Flow (PKCE)

1.  User opens LIFF App.
2.  LIFF App requests backend (`/liff/init`) to check link status.
3.  If not linked, User clicks "Link Google Account".
4.  LIFF App requests backend (`/liff/auth/google`).
5.  Backend generates PKCE codes (`code_verifier`, `code_challenge`) and `state`. Stores `code_verifier` temporarily (e.g., Firestore with TTL).
6.  Backend redirects User to Google Auth URL (with `code_challenge`, `state`).
7.  User authenticates and grants permission on Google.
8.  Google redirects User to backend callback (`/auth/google/callback`) with `code` and `state`.
9.  Backend verifies `state`, retrieves `code_verifier`.
10. Backend exchanges `code` and `code_verifier` for tokens (Access Token, Refresh Token) with Google, using Client Secret from Secret Manager.
11. Backend encrypts Refresh Token using key from Secret Manager.
12. Backend saves encrypted Refresh Token, email, expiry etc. to Firestore, linked to `line_user_id`.
13. Backend redirects User back to LIFF App with success/failure status.

### Message Processing Flow (Initial Release)

1.  User sends message via LINE.
2.  LINE Platform sends Webhook event to Cloud Run (`/webhook`).
3.  Cloud Run verifies signature.
4.  Cloud Run immediately returns `200 OK` to LINE Platform.
5.  Cloud Run adds event processing to Background Task (or Cloud Task for longer processing).
6.  Background Task:
    a.  Retrieves user info and valid Google Credentials (refreshing if needed) from Firestore/Secret Manager.
    b.  Passes message text to NLP Engine.
    c.  NLP Engine parses intent and extracts entities (datetime, title, etc.).
    d.  Based on intent/entities, calls appropriate service (e.g., `GoogleCalendarService`).
    e.  `GoogleCalendarService` interacts with Google Calendar API.
    f.  Generates reply message(s).
    g.  Sends reply message(s) to user via LINE Messaging API.

### Reminder Flow

1.  **Cloud Scheduler** triggers a job (e.g., daily morning reminder check).
2.  Scheduler job adds a task to **Cloud Tasks** queue, targeting a Cloud Run endpoint (e.g., `/tasks/generate-reminders`).
3.  Cloud Run task handler:
    a.  Queries Firestore for users with reminders enabled for that time.
    b.  For each user, retrieves upcoming events from Google Calendar API (using valid credentials).
    c.  Formats reminder messages.
    d.  Adds individual reminder sending tasks to another **Cloud Tasks** queue (targeting `/tasks/send-reminder`).
4.  Cloud Tasks executes individual reminder sending tasks:
    a.  Cloud Run task handler (`/tasks/send-reminder`) receives task payload (user ID, message).
    b.  Sends Push Message to the user via LINE Messaging API.
    c.  Updates reminder status in Firestore (optional).

## 4. Error Handling & Logging

-   **Cloud Logging:** All application logs (INFO, WARNING, ERROR) are sent to Cloud Logging, preferably in structured (JSON) format. Include `trace_id`, `line_user_id` where possible.
-   **Cloud Monitoring:** Monitor key metrics (Cloud Run latency/errors, Task queue length/failures, Firestore latency/errors). Set up alerts for anomalies.
-   **FastAPI Exception Handlers:** Define custom exception handlers in FastAPI to catch specific application errors (e.g., AuthenticationError, CalendarAPIError) and return appropriate HTTP responses while logging detailed error info.
-   **Cloud Tasks Retries:** Configure Cloud Tasks queues with appropriate retry policies for transient errors. Implement dead-letter queues for persistent failures.
-   **User Feedback:** Provide clear, user-friendly error messages via LINE, avoiding technical details. Log detailed errors internally.

## 5. Security Patterns

-   **Secret Management:** Use GCP Secret Manager for all sensitive credentials. Grant minimal necessary IAM permissions to the Cloud Run service account.
-   **Authentication:** Implement OAuth 2.0 PKCE flow for Google authentication. Verify LINE webhook signatures.
-   **Authorization:** Use Firestore Security Rules to restrict data access. Ensure Cloud Run service account has appropriate (but not excessive) permissions.
-   **Data Encryption:** Encrypt sensitive data at rest (e.g., refresh tokens in Firestore) using keys managed in Secret Manager. Use HTTPS for all communication (default for Cloud Run).
-   **Input Validation:** Use Pydantic models in FastAPI for request body validation. Sanitize user input before processing or logging.
-   **Rate Limiting:** Implement application-level rate limiting if necessary, in addition to relying on API provider limits. Monitor API usage.
-   **Dependency Scanning:** Integrate vulnerability scanning for dependencies into the CI/CD pipeline.
