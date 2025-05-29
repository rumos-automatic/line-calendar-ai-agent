# Active Context (GCP Migration Phase)

*2025年4月14日 更新: GCP移行計画と段階的NLP導入方針を反映*

## Current Focus
- **GCP環境構築:** Cloud Run, Firestore, Secret Manager, Cloud Tasks, Cloud Scheduler のセットアップと設定。
- **CI/CDパイプライン構築:** GitHub Actionsを用いたテスト、ビルド、デプロイの自動化。
- **Docker化:** アプリケーションのDockerイメージ作成とローカルDocker Compose環境整備。
- **コア機能実装 (初期リリース向け):**
    - LINE Webhook処理 (FastAPI + BackgroundTasks)
    - LINE LIFF連携 (認証フロー開始、設定画面連携)
    - Google OAuth認証 (PKCEフロー、Firestore + Secret Managerでのトークン管理)
    - Google Calendar基本連携 (CRUD操作)
    - パターン認識ベースのNLPエンジン実装 (`nlp/`)
    - リマインダー機能 (Cloud Tasks/Scheduler連携)
- **テスト基盤整備:** `pytest`, Firestoreエミュレータ, モックライブラリ導入。

## Recent Changes
- **ドキュメント整備:**
    - 過去の開発経験を `LESSONS_LEARNED.md` に整理。
    - `カレンダーLINE連携要件定義.md` をGCP前提、段階的NLP導入方針で改訂。
    - GCPベースの `SYSTEM_DESIGN_GCP.md` を新規作成。
    - `DEVELOPMENT_NOTES.md` に開発・運用上の注意点を追記。
    - 各API実装ガイド (`GoogleカレンダーAPI実装ガイド.txt`, `LINE連携 最新実装ガイド.txt`, `OpenAI agents SDK導入ガイド.txt`) を最新方針に合わせて更新。
    - `README.md` をプロジェクト概要、新アーキテクチャ、セットアップ手順中心に刷新。
- **開発方針決定:**
    - インフラ基盤をGCPに移行。
    - データベースをFirestoreに変更。
    - 非同期処理にCloud Tasks/Schedulerを採用。
    - 自然言語処理は初期リリースではパターン認識ベースとし、OpenAI Agents SDKはリリース後に導入検討。
    - 認証フローにPKCEを採用。
    - CI/CDを導入。

## Next Steps (Initial Release Focus)
1.  **GCP環境セットアップ:** 必要なGCPサービスを有効化し、IAM権限、APIキー、OAuthクライアント等を設定。Secret Managerにシークレットを登録。
2.  **ローカル開発環境整備:** Docker Compose設定 (`docker-compose.yml`) を作成し、FastAPIアプリとFirestoreエミュレータを起動できるようにする。`.env.example` を整備。
3.  **CI/CDパイプライン初期設定:** GitHub Actionsワークフロー (`.github/workflows/deploy.yml`) を作成し、Lint, テスト, Dockerビルド, Artifact Registryへのプッシュまでを自動化。
4.  **認証フロー実装:** LINE LIFFからのGoogle OAuth開始、PKCEフロー、コールバック処理、Firestoreへの暗号化トークン保存を実装 (`auth_service.py`, `repositories/user_repository.py`, `routers/liff.py`)。
5.  **Webhook実装:** LINE Messaging APIからのWebhookを受信し、署名検証、イベント処理（初期はメッセージ受信のみ）を行うエンドポイントを実装 (`routers/line_webhook.py`)。バックグラウンド処理を活用。
6.  **パターン認識NLP実装:** 日時表現解析 (`nlp/datetime_patterns.py`) と基本的な意図・情報抽出ロジック (`nlp/parser.py`, `services/nlp_service.py`) を実装。
7.  **カレンダー連携実装:** Google Calendar APIのCRUD操作を行うサービス (`services/google_calendar_service.py`) を実装。認証情報取得処理 (`get_valid_credentials`) と連携。
8.  **メッセージ処理実装:** NLP解析結果に基づきカレンダー操作を実行し、応答メッセージを生成するロジック (`services/message_handler.py`) を実装。
9.  **リマインダー実装:** Cloud Schedulerで定期ジョブを設定し、Cloud Tasks経由でリマインダー生成・送信タスクを実行する仕組みを実装 (`routers/tasks.py`, `services/reminder_service.py`)。
10. **テスト実装:** 各コンポーネントの単体テスト、結合テスト（エミュレータ使用）を実装 (`tests/`)。
11. **ステージング環境デプロイ:** CI/CD経由でステージング環境のCloud Runにデプロイし、動作確認。
12. **本番環境デプロイ:** ステージングでの検証後、本番環境へデプロイ。

## Active Decisions
- **Cloud Platform:** GCPを採用。
- **Runtime:** Cloud Run (Dockerコンテナ)。
- **Database:** Firestore (NoSQL)。
- **Async Processing:** Cloud Tasks & Cloud Scheduler。
- **Secret Management:** GCP Secret Manager。
- **Authentication:** LINE Login + Google OAuth 2.0 with PKCE via LIFF。
- **NLP Approach:** Phased approach - Pattern Matching first, consider OpenAI Agents SDK later.
- **CI/CD:** GitHub Actions.
- **Backend Framework:** FastAPI (Python).

## Current Patterns
- Repository Pattern (Firestore access)
- Service Layer Pattern (Business logic)
- Dependency Injection (FastAPI)
- Strategy Pattern (Initial NLP parsing)
- Asynchronous Task Queue (Cloud Tasks)
- Scheduled Jobs (Cloud Scheduler)
- Secure Credential Management (Secret Manager)
- Infrastructure as Code (Implicit via gcloud/Terraform in CI/CD, though not explicitly defined yet)

## Recent Learnings (Summary from LESSONS_LEARNED.md)
- 環境差異（ローカル vs Cloud Run）は問題の元。Docker化とCI/CDが重要。
- API/SDKのバージョンアップ追従は必須。ドキュメント精読とテストが不可欠。
- OAuth認証とトークン管理は複雑。PKCE採用、暗号化保存、自動更新が鍵。
- 設定管理は環境変数とSecret Managerを使い分ける。起動時の読み込み順序に注意。
- 非同期処理は状態管理とエラー監視が重要。Cloud Tasks/Schedulerが有効。
- Firestore移行はデータアクセス層の抽象化が役立つ。
- パターン認識NLPは網羅性と拡張性が重要。
- 詳細なロギングと監視アラートは迅速な問題解決に不可欠。

## Important Considerations
- **GCP Costs:** Monitor usage of Cloud Run, Firestore, Tasks, Logging, etc. Optimize where possible.
- **Secret Management Security:** Ensure proper IAM permissions for Secret Manager access. Rotate encryption keys periodically if required.
- **Firestore Schema Design:** While flexible, plan the data structure for efficient querying and potential future needs. Define indexes appropriately.
- **Async Task Monitoring:** Closely monitor Cloud Tasks execution, failures, and queue lengths via Cloud Logging/Monitoring. Implement robust error handling and retries.
- **NLP Pattern Coverage:** Continuously evaluate and expand the patterns covered by the initial NLP engine based on user input logs. Ensure maintainability.
- **Scalability Limits:** Understand potential bottlenecks (API rate limits, Firestore hot spots, Cloud Run instance limits) and plan accordingly.
- **Cold Starts (Cloud Run):** Be aware of potential cold start latency, especially if using min-instances=0. Optimize container startup time if necessary.
