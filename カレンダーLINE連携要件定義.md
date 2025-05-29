# GoogleカレンダーとLINE連携 スケジュール管理エージェント
要件定義書 | 2025年4月7日

## 0. 主要技術の説明

### OpenAI Agents SDKとは？
OpenAI Agents SDKは、AIエージェントを効率的に構築するためのソフトウェア開発キットです。従来のAPIが単一の機能を呼び出すだけのインターフェースを提供するのに対し、Agents SDKは複数のAPIやツールを連携させ、AIが状況に応じて適切なツールを自動選択して使用できる仕組みを提供します。これにより、複雑なタスクを段階的に解決する能力を持つインテリジェントなAIアプリケーションの開発が可能になります。

**通常のAPIとの主な違い：**
- 従来のAPI：個別の機能を呼び出すための単一インターフェース
- Agents SDK：複数のツールやAPIを組み合わせ、AIが自律的に適切なツールを選択・実行
- タスクの分解と連鎖処理が可能で、AIの思考プロセスのトレースも可能

### LINE LIFFとは？
LINE Front-end Framework（LIFF）は、LINEアプリ内でWebアプリケーションを実行できるプラットフォームです。これにより、ユーザーはLINEアプリを離れることなく、Webの機能を利用できます。

**LINE LIFFを使用する理由：**
- ユーザーがLINEアプリを離れることなく、GoogleアカウントのOAuth認証が完結
- LINE IDの自動取得により、LINE IDとGoogleアカウントの紐付けが容易
- シームレスなユーザー体験の提供（アプリ切り替えの手間がない）
- セキュアな認証プロセスの実現
- ユーザーの離脱率低減

## 1. プロジェクト概要

OpenAI Agents SDKを活用し、GoogleカレンダーとLINEを双方向に連携させたスケジュール管理AIエージェントを開発する。ユーザーはLINEを通じて自然言語で予定を追加・確認でき、GoogleカレンダーからLINEへの通知も可能とする。

**プロジェクト目標：** LINEとGoogleカレンダー間のシームレスな予定管理を実現し、ユーザーの生産性向上を支援する

### 主な機能
- LINEからGoogleカレンダーへの予定追加
- Googleカレンダーの予定をLINEに通知
- 自然言語での予定操作（追加・確認・変更・削除）
- 定期的な予定確認リマインド

## 2. 機能要件

### コア機能概要
- GoogleカレンダーとLINEの双方向連携
- 自然言語によるカレンダー操作（追加・確認・編集・削除）
- カスタマイズ可能なリマインド機能
- 直感的なユーザーインターフェース

### LINE側の機能
- 自然言語での予定入力・解析
- 日時が曖昧な入力の解決（「明日の午後」など）
- 予定追加時の確認メッセージ
- 予定リスト表示（日別・週別・月別）
- 自然言語での予定確認（「今日の予定は？」「明日の予定は？」などの問いかけに対応）
- 予定詳細の確認
- 予定の編集・削除
- カスタマイズ可能なリマインド機能
  - 指定時間でのリマインド設定（当日9:00、前日22:00など）
  - 指定期間の予定まとめ（1日分のみ、3日分、一週間分など）
  - リマインド頻度の設定

### Googleカレンダー側の機能
- 予定の自動同期
- 予定変更時のLINE通知
- カレンダー上でタグ付け（LINEから追加された予定）
- 複数カレンダー対応（個人/仕事など）

### AI機能
- 自然言語からの予定情報抽出
- あいまいな表現の解決（「来週の水曜日」→日付変換）
- 自然言語での予定照会解析（「明後日の午後の予定は？」などの質問理解）
- 予定の重複確認と提案
- 優先度の自動判定
- 関連予定のグルーピング提案
- 類似表現の理解（「予定を教えて」「スケジュールは？」など多様な表現に対応）

## 3. 技術スタック

### フロントエンド
- LINE Messaging API
- LINE LIFF（ユーザー認証・連携用）
- HTML/CSS/JavaScript（LIFF画面）
- レスポンシブデザイン

### バックエンド
- 言語: Python
- フレームワーク: FastAPI/Flask
- OpenAI Agents SDK
- GoogleカレンダーAPI
- LINE Login API
- LINE LIFF SDK
- OAuth 2.0クライアント

### インフラ (GCP前提)
- **実行環境:** Google Cloud Run (コンテナベース、フルマネージド)
- **データベース:** Google Cloud Firestore (NoSQL, スケーラブル)
- **認証:** OAuth 2.0 (Google Identity Platform, LINE Login)
- **シークレット管理:** Google Cloud Secret Manager (APIキー、トークン等の機密情報保管)
- **非同期処理:** Google Cloud Tasks / Cloud Scheduler (リマインダー等のバックグラウンド処理)
- **コンテナレジストリ:** Google Cloud Artifact Registry (Dockerイメージ保管)
- **CI/CD:** GitHub Actions (テスト、ビルド、デプロイ自動化)
- **監視・ロギング:** Google Cloud Logging, Cloud Monitoring (運用監視、アラート)
- **ネットワーク:** Cloud RunのデフォルトHTTPS、必要に応じてVPC Connector

### データベース設計 (Firestore)
**users コレクション:**
- ドキュメントID: `line_user_id`
- フィールド:
  - `google_email`: String
  - `google_refresh_token_encrypted`: String (Secret Manager等で管理される鍵で暗号化)
  - `google_token_expiry`: Timestamp
  - `calendars_access`: Array<String> (アクセス可能なカレンダーIDリスト)
  - `preferences`: Map (リマインダー設定など)
    - `reminder_enabled`: Boolean
    - `reminder_time_morning`: String (HH:MM)
    - `reminder_time_evening`: String (HH:MM)
    - `reminder_days_ahead`: Integer
    - `reminder_before_event_minutes`: Integer
  - `created_at`: Timestamp
  - `last_updated`: Timestamp
  - `is_active`: Boolean (ユーザーが有効か)

**reminders コレクション (Cloud Tasks/Schedulerで利用):**
- ドキュメントID: 自動生成 or `line_user_id` + `event_id`
- フィールド:
  - `line_user_id`: String
  - `event_id`: String (Google Calendar Event ID)
  - `reminder_time`: Timestamp (通知実行時刻)
  - `message`: String (通知内容)
  - `status`: String (pending, sent, failed)
  - `created_at`: Timestamp

**採用技術の理由：**
- OpenAI Agents SDKは自然言語処理と複数APIの連携に最適。
- Python + FastAPIはCloud Runとの親和性が高く、非同期処理に適している。
- Firestoreはスケーラビリティと柔軟性に優れ、サーバーレス環境に適している。
- GCPのマネージドサービスを活用し、インフラ管理の負担を軽減する。

## 4. システム構成

### データフロー図
**認証フロー：**
ユーザー → LINE Bot → LINE LIFF → Google OAuth → バックエンドサーバー → ユーザーDB (紐付け保存)

**通常利用フロー：**
ユーザー → LINE → Webhook → バックエンドサーバー → OpenAI Agents SDK → GoogleカレンダーAPI

### コンポーネント構成 (GCPサービス連携)
- **LINE Bot (UI):** ユーザーとの対話インターフェース
- **Cloud Run Service (Backend):**
  - Webhookエンドポイント (LINEからのメッセージ受信)
  - LIFF関連エンドポイント (認証処理)
  - APIエンドポイント (内部処理用)
- **AI Agent (OpenAI Agents SDK):** 自然言語処理、意図解釈、ツール実行
- **Calendar Connector:** Google Calendar APIとの連携ロジック
- **Notification Manager:**
  - Cloud Scheduler: 定期的なリマインダータスクのトリガー
  - Cloud Tasks: 個別リマインダーのキューイングと実行依頼
- **Firestore (Database):** ユーザー情報、設定、リマインダー状態の永続化
- **Secret Manager:** APIキー、OAuthクライアントシークレット、暗号化キーの保管
- **Cloud Logging/Monitoring:** ログ収集、パフォーマンス監視、アラート

### 認証フロー（LINE LIFF + GCP）
- Googleアカウント連携（OAuth 2.0 PKCEフロー推奨）
- LINE LIFF画面でのユーザー認証とLINE ID取得
- LINE IDとGoogleアカウント情報の紐付け（Firestoreに保存）
- アクセストークン・リフレッシュトークン管理
  - リフレッシュトークンは **Secret Manager** に保存された鍵で暗号化しFirestoreに保存
  - アクセストークンは有効期限と共にFirestoreに保存（または必要に応じて都度取得）
- 定期的なトークン更新処理（Cloud Scheduler/Tasksでバッチ処理 or 必要に応じてオンデマンド）

**LINE LIFF活用ポイント：**
- LINEアプリ内でシームレスな認証体験
- LINE IDの自動取得とGoogleアカウント連携
- アクセス権限管理の透明性確保

## 5. 非機能要件 (GCP環境前提)

### パフォーマンス
- **応答時間:**
  - LINEメッセージ応答（同期処理）: 平均 3秒以内、最大 5秒以内
  - 予定登録完了（非同期含む）: ユーザーへの初期応答は3秒以内、バックグラウンド処理完了は15秒以内
- **スケーラビリティ:**
  - Cloud Runの自動スケーリング設定により、負荷に応じてインスタンス数を自動調整 (初期: min 0, max 10程度から調整)
  - Firestoreは自動でスケールするため、データベース起因のボトルネックは少ない想定
- **目標同時接続ユーザー:** 初期 100人、将来的には1000人以上を目指す

### セキュリティ
- **認証・認可:**
  - OAuth 2.0 (PKCEフロー) を適切に実装
  - LINE, Googleからのリクエスト検証 (署名検証、IDトークン検証)
- **機密情報管理:**
  - APIキー、OAuthクライアントシークレット、DB接続情報、暗号化キー等は **Google Cloud Secret Manager** で管理
  - アプリケーションからはIAM権限に基づき実行時に取得
- **データ保護:**
  - リフレッシュトークン等の機密性の高いユーザーデータは、Secret Managerで管理する鍵を用いてアプリケーションレベルで暗号化してFirestoreに保存
  - Firestoreのセキュリティルールを設定し、不正アクセスを防止
  - 通信はすべてHTTPSで暗号化 (Cloud Runデフォルト)
- **脆弱性対策:**
  - 依存ライブラリの脆弱性スキャンをCI/CDプロセスに組み込む (例: `pip-audit`, Snyk)
  - 入力値バリデーションの徹底 (FastAPIのPydanticモデル活用)
  - 一般的なWeb脆弱性対策 (OWASP Top 10参照)

### 可用性・信頼性
- **サービス稼働率:** 目標 99.9% (Cloud RunのSLAに基づく)
- **障害復旧:**
  - Cloud RunはマルチAZ構成で自動フェイルオーバー
  - Firestoreもマルチリージョン/デュアルリージョン構成を選択可能 (要件に応じて検討)
  - エラー発生時はCloud Loggingに詳細ログを出力し、Cloud Monitoringでアラートを設定
- **バックアップ:**
  - FirestoreはPoint-in-Time Recovery (PITR) を有効化し、過去7日間(設定可能)の任意の時点に復元可能にする
  - 定期的なエクスポートも検討 (Cloud Storageへ)
- **ヘルスチェック:** Cloud Runのヘルスチェックエンドポイントを実装し、異常なインスタンスを自動的に置き換える

### 拡張性
- **インフラ:** Cloud Run, Firestoreともに負荷に応じた自動スケールが可能
- **アプリケーション:** モジュール化された設計により、機能追加・変更が容易
- **データベース:** Firestoreのスキーマレスな特性を活かし、将来的なデータ構造の変更に対応しやすい
- **他サービス連携:** Google Calendar以外のカレンダーサービスへの対応も、コネクタ部分の差し替えで実現可能

### 運用・保守性
- **デプロイ:** GitHub Actionsを用いたCI/CDパイプラインによる自動デプロイ
- **監視:** Cloud LoggingとCloud Monitoringによるログ収集、メトリクス監視、アラート設定
- **設定管理:** 環境変数とSecret Managerによる設定の一元管理
- **ドキュメント:** Memory Bankシステムによる継続的なドキュメント更新

## 6. ユーザー設定と通知機能 (変更なし)

### リマインド設定
- **時間指定オプション**
  - 予定当日の指定時間（例：当日9:00）
  - 予定前日の指定時間（例：前日22:00）
  - 予定の指定時間前（例：1時間前、30分前）
  - カスタム設定（曜日・時間の組み合わせなど）

- **期間指定オプション**
  - 1日分の予定まとめ
  - 3日分の予定まとめ
  - 1週間分の予定まとめ
  - 月間予定概要
  - カスタム期間設定

- **通知形式オプション**
  - テキスト形式
  - リスト形式
  - カレンダービュー形式
  - 重要度別ハイライト

### 自然言語インターフェース
- **予定照会コマンド例**
  - 「今日の予定は？」
  - 「明日の午後に何がある？」
  - 「今週末の予定を教えて」
  - 「次の会議はいつ？」
  - 「明後日から一週間の予定リスト」

- **予定管理コマンド例**
  - 「明日の会議をキャンセルして」
  - 「水曜日の予定を金曜日に変更」
  - 「来週の月曜に営業会議を追加して」
  - 「明日のランチミーティングの時間を13時に変更」

## 7. リスクと対策 (改訂版)

### 主なリスクと対策
- **[高] 環境差異によるデプロイ問題:**
  - **リスク:** ローカル開発環境とCloud Run本番環境の違い（特に環境変数、依存関係）により、デプロイ後に予期せぬエラーが発生する。
  - **対策:**
    - **Docker化:** 開発初期からDockerfileを作成し、ローカルでもDockerコンテナ内で開発・テストを行う。
    - **CI/CD:** GitHub Actionsでテスト・ビルド・デプロイを自動化し、一貫したプロセスを保証する。
    - **ステージング環境:** GCP上に本番に近いステージング環境を構築し、デプロイ前に検証を行う。
    - **設定管理:** 環境変数はCloud Runの機能とSecret Managerで管理し、アプリケーションコードから分離する。
- **[高] API/SDKの仕様変更・バージョン追従:**
  - **リスク:** LINE, Google, OpenAIのSDK/API仕様変更により、既存機能が動作しなくなる。
  - **対策:**
    - **定期的な確認:** 各SDK/APIの公式ドキュメントやリリースノートを定期的に確認する体制を作る。
    - **依存関係管理:** `requirements.txt` でバージョンを固定し、意図しないアップデートを防ぐ。更新時は十分なテストを行う。
    - **抽象化レイヤー:** API連携部分にアダプターパターンなどを導入し、変更の影響範囲を局所化する。
- **[高] 認証トークンの管理不備:**
  - **リスク:** トークンの漏洩、失効、不正利用によるセキュリティインシデントや機能停止。
  - **対策:**
    - **Secret Manager:** 機密性の高いクライアントシークレットや暗号化キーはSecret Managerで管理。
    - **暗号化:** リフレッシュトークンはアプリケーションレベルで暗号化して保存。
    - **自動更新:** トークン有効期限を監視し、期限前にリフレッシュトークンを用いて自動更新する仕組みを実装（Cloud Scheduler/Tasks活用）。
    - **権限最小化:** APIアクセスに必要なスコープを最小限にする。
- **[中] APIレート制限超過:**
  - **リスク:** Google Calendar API等の利用制限を超え、一時的に機能が利用できなくなる。
  - **対策:**
    - **効率的なAPI利用:** キャッシュ活用、バッチ処理、Webhook利用（可能な場合）などでAPI呼び出し回数を削減。
    - **リトライ戦略:** レート制限エラー発生時に指数バックオフを用いたリトライ処理を実装。
    - **監視:** API利用状況を監視し、制限に近づいたらアラートを出す。
- **[中] 自然言語解釈の精度限界:**
  - **リスク:** ユーザーの多様な日本語表現を完全に解釈できず、誤った予定登録や操作が発生する。
  - **対策:**
    - **対応範囲の明確化:** 対応可能な日時表現やコマンドのパターンをドキュメント化し、ユーザーに明示する。
    - **確認フロー:** 解釈に曖昧さが残る場合や、重要な操作（削除など）の前に、ユーザーに確認を求めるステップを入れる。
    - **継続的な改善:** ユーザーの入力ログを分析し、対応パターンやAIモデル（OpenAI Agents SDK）を継続的に改善する。
- **[中] 非同期処理（リマインダー等）の失敗:**
  - **リスク:** Cloud Tasks/Schedulerのタスク実行失敗により、リマインダーが送信されない。
  - **対策:**
    - **リトライ設定:** Cloud Tasksの自動リトライ設定を活用。
    - **エラー監視:** タスク失敗時にCloud Loggingにエラーを出力し、Cloud Monitoringでアラートを設定。
    - **冪等性確保:** タスクが複数回実行されても問題ないように設計する。
    - **状態管理:** タスクの実行状態（pending, success, failed）をFirestoreで管理し、追跡可能にする。

### 開発スケジュール (目安)
- **フェーズ1:** 設計見直しとGCP環境構築・CI/CD設定（1-2週間）
- **フェーズ2:** Dockerベース開発環境整備とコア機能（認証、Webhook）実装（2週間）
- **フェーズ3:** カレンダー連携・自然言語処理実装（OpenAI Agents SDK）（3週間）
- **フェーズ4:** リマインダー機能実装（Cloud Tasks/Scheduler）（2週間）
- **フェーズ5:** ステージング環境テストと改善（2週間）
- **フェーズ6:** 本番デプロイと監視体制構築（1週間）

### 実装優先順位 (変更なし)
1. LINE LIFF認証画面と紐付け機能 (GCP Secret Manager連携含む)
2. LINE → Googleカレンダー連携 (基本CRUD)
3. 自然言語解析機能 (OpenAI Agents SDK)
   - 予定追加・編集・削除機能
   - 自然言語による予定照会機能
4. カスタマイズ可能なリマインド機能 (Cloud Tasks/Scheduler連携)
5. Googleカレンダー → LINE通知 (Webhook or 定期ポーリング)
6. 高度な予定管理機能

### LINE LIFF実装詳細 (変更なし)
- LIFF ID取得とLINE Developersコンソール設定
- LIFF EndpointのURL設定（Callback URL）
- ログイン状態の永続化（localStorageなど）
- モバイル・デスクトップ両対応UI
- 初回連携完了後のガイド表示

## 8. 開発・運用プロセス (新規追加)

### 開発環境
- ローカル環境: Docker Composeを使用し、Cloud Run環境を可能な限り再現する。
- 各開発者は個別のGCPプロジェクトまたはエミュレータを使用し、Firestore, Secret Manager等をテストする。

### バージョン管理
- Gitを使用し、GitHubでリポジトリを管理する。
- ブランチ戦略: GitflowまたはGitHub Flowを採用する。
- コミットメッセージ規約: Conventional Commitsなどを参考に規約を定める。

### CI/CD (Continuous Integration / Continuous Deployment)
- GitHub Actionsを使用する。
- **CI:** プルリクエスト作成時やmainブランチへのマージ時に自動実行。
  - Lintチェック (flake8, black)
  - 単体テスト・結合テスト (pytest)
  - 依存関係の脆弱性スキャン
  - Dockerイメージのビルド
- **CD:** mainブランチへのマージ後、自動実行。
  - DockerイメージをArtifact Registryにプッシュ
  - ステージング環境への自動デプロイ
  - (手動承認を経て) 本番環境への自動デプロイ

### テスト戦略
- **単体テスト:** 各モジュール・関数単位のテスト (pytest, mock)
- **結合テスト:** 複数モジュール連携のテスト (Docker Compose環境下で実行)
- **E2Eテスト:** ステージング環境で実際のLINE/Google APIと連携させたテスト (手動 or 自動化ツール)
- **カバレッジ:** テストカバレッジを計測し、一定基準 (例: 80%以上) を維持する。

### 環境管理
- **開発 (Development):** ローカルDocker環境 or 個別GCPプロジェクト
- **ステージング (Staging):** 本番環境とほぼ同等のGCP環境 (Cloud Run, Firestore等)
- **本番 (Production):** ユーザー向けGCP環境
- 環境ごとの設定値は環境変数とSecret Managerで管理する。

### 監視・ロギング
- Cloud Logging: アプリケーションログ、アクセスログ、エラーログを収集・検索可能にする。構造化ログを採用する。
- Cloud Monitoring: 主要メトリクス (リクエスト数、レイテンシ、エラー率、CPU/メモリ使用率、タスクキュー長など) を監視し、ダッシュボードを作成する。
- アラート: 異常値やエラー発生時に、指定されたチャンネル (Slack, Email等) に通知するアラートを設定する。

### ドキュメント
- Memory Bankシステムを継続的に活用し、設計、決定事項、運用手順などを記録する。
- README.md は常に最新の状態を保つ。
