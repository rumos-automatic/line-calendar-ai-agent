# 開発・運用に関する追加メモ

このドキュメントは、`LESSONS_LEARNED.md`, `カレンダーLINE連携要件定義.md`, `SYSTEM_DESIGN_GCP.md` を補完し、次回の開発サイクルや運用において特に留意すべき点をまとめたものです。

## 1. テスト戦略の詳細

-   **外部API連携のテスト:**
    -   **モック/スタブ:** `unittest.mock` (Python標準) や `requests-mock` ライブラリを活用し、単体・結合テストフェーズで外部APIへの依存を排除する。LINE Messaging API, Google Calendar API, OpenAI APIのレスポンスを模倣する。
    -   **テスト用アカウント/環境:** 可能であれば、LINE、Google、OpenAIのテスト用アカウントやサンドボックス環境を用意し、ステージング環境でのE2Eテストに利用する。
    -   **レート制限考慮:** モックを使わないテスト（ステージング等）では、APIのレート制限に達しないよう注意する。テスト実行頻度や並列度を調整する。
-   **非同期処理 (Cloud Tasks) のテスト:**
    -   **ローカル:** Cloud Tasksエミュレータは公式には提供されていないため、ローカルテストではタスクキューイング部分をモックするか、タスク処理ロジックを直接呼び出すテストケースを作成する。
    -   **ステージング:** 実際のCloud Tasksと連携させ、タスクのキューイング、実行、リトライ、エラーハンドリングが意図通り動作するかを検証する。タスクペイロードや実行タイミングの確認が重要。
-   **Firestoreのテスト:**
    -   **Firestoreエミュレータ:** ローカル開発やCI環境でFirestoreエミュレータを使用し、実際のFirestoreへの接続なしにデータベース操作のテストを行う。`google-cloud-firestore` ライブラリはエミュレータ接続に対応している。
    -   **テストデータ管理:** テスト実行前にクリーンな状態にし、テスト後にデータを削除する仕組みを確立する（テスト用DBインスタンス分離、データ削除スクリプトなど）。

## 2. エラーハンドリングとロギング戦略

-   **構造化ログ:** Cloud Loggingで効率的に検索・分析できるよう、ログはJSON形式などの構造化ログで出力する。Pythonの `logging` モジュールと `python-json-logger` などのライブラリを活用する。
-   **必須ログフィールド:** すべてのログエントリに最低限以下の情報を含めることを推奨。
    -   `timestamp`: ログ発生日時
    -   `severity`: ログレベル (INFO, WARNING, ERROR, CRITICAL)
    -   `message`: ログメッセージ本文
    -   `trace_id`: リクエストや処理のトレースID (OpenTelemetry等で自動付与推奨)
    -   `line_user_id`: (可能な場合) 関連するユーザーID
    -   `service_context`: サービス名 (Cloud Run)
    -   `version`: アプリケーションバージョン
-   **エラーログ:** 例外発生時には、スタックトレースに加え、関連するリクエスト情報（エンドポイント、メソッド、ペイロードの一部など）や処理中の状態変数を含める。
-   **アラート戦略:** Cloud Monitoringで以下の項目に基づきアラートを設定する。
    -   Cloud RunのHTTPエラー率 (5xx) の急増
    -   Cloud Runのレイテンシ増加
    -   Cloud Tasksの失敗タスク数の増加
    -   特定のERRORレベルログの頻発
    -   (必要に応じて) Firestoreのレイテンシ増加やエラー
-   **ユーザーへのエラー通知:** システムエラーが発生した場合、ユーザーには「現在処理を完了できませんでした。しばらくしてからもう一度お試しください。」のような汎用的なメッセージを返し、内部的には詳細なエラーログを記録して調査可能にする。特定のエラー（認証切れなど）は、ユーザーに具体的なアクション（再連携など）を促すメッセージを返す。

## 3. 設定管理のベストプラクティス

-   **Secret Manager vs 環境変数:**
    -   **Secret Manager:** APIキー、OAuthクライアントシークレット、DBパスワード、トークン暗号化キーなど、特に機密性の高い情報に使用。IAMでアクセス制御を行う。
    -   **環境変数 (Cloud Run):** デプロイ環境ごとの設定値（`DATABASE_TYPE`, `ENVIRONMENT` (staging/production), 外部サービスのURLなど）、Secret Managerから取得したシークレットを参照する変数名などに使用。**注意:** 環境変数自体に機密情報を直接書き込まない。
-   **ローカル開発 (Docker Compose):**
    -   `.env` ファイルを使用して環境変数を管理する。
    -   `.env.example` ファイルを用意し、必要な環境変数を明記する。
    -   `.env` ファイルは `.gitignore` に追加し、リポジトリにコミットしない。
    -   ローカルテスト用にSecret Managerのエミュレーションやダミー値を使用する。
-   **設定の反映:** Cloud Runの環境変数やシークレット参照を変更した場合、新しいリビジョンをデプロイする必要がある。アプリケーション内で設定値をキャッシュしている場合は、再起動やキャッシュクリアが必要になることがある。

## 4. GCPコスト意識

-   **主要サービスの課金体系:**
    -   **Cloud Run:** CPU/メモリ使用時間、リクエスト数。アイドル時は最小インスタンス数（0も可）によりコスト削減可能。
    -   **Firestore:** ドキュメントの読み取り/書き込み/削除回数、ストレージ容量、ネットワーク帯域。インデックス設計が読み取りコストに影響。
    -   **Cloud Tasks:** タスク数、ネットワーク帯域。
    -   **Cloud Scheduler:** ジョブ数。
    -   **Secret Manager:** アクセス回数、シークレットバージョン数。
    -   **Cloud Logging/Monitoring:** 取り込みログ量、保存期間、実行された指標読み取り/API呼び出し。無料枠を超えると課金。
    -   **OpenAI API:** 使用するモデルと入出力トークン数。
-   **コスト監視:** GCPコンソールの請求レポートや予算アラートを設定し、予期せぬコスト増を早期に検知する。サービスごとにラベルを付けてコストを分類する。
-   **最適化ポイント:**
    -   Firestore: 不要な読み書きを避ける。適切なインデックスを作成する（複合インデックスはコスト増要因にもなりうる）。
    -   Cloud Run: 最小/最大インスタンス数を適切に設定。CPU割り当てを最適化。
    -   Logging: 不要なログ（例: DEBUGレベル）を本番環境では抑制する。ログの除外フィルタを設定する。
    -   OpenAI: プロンプトを簡潔にする。必要なツールのみを定義する。レスポンス形式を制御する。

## 5. OpenAI Agents SDKの注意点

-   **SDKバージョン:** 開発が活発なため、バージョン間の互換性に引き続き注意が必要。アップデート時は変更点を十分に確認し、テストを行う。
-   **プロンプトとツール設計:** エージェントの性能はプロンプトとツールの設計に大きく依存する。明確で具体的な指示、適切なツール説明、期待される出力形式の指定が重要。試行錯誤と評価が必要。
-   **エラーハンドリング:** ツール実行時のエラー（APIエラー、データ処理エラーなど）をエージェントが適切にハンドリングし、ユーザーにフィードバックできるような設計を心がける。
-   **トークン使用量:** 複雑な会話や多数のツール呼び出しはトークン使用量を増加させる。コンテキスト管理（会話履歴の要約や制限）、ツールの効率的な設計、レスポンス長の制御などで最適化を図る。コストと性能のバランスを考慮する。

## 6. 段階的NLPアプローチに関する注意点

-   **初期リリース (パターン認識ベース):**
    -   **網羅性:** 対応する日時表現やコマンドのパターンをできるだけ幅広く定義することが重要。特に日本語の日時表現 (`datetime_patterns.py` など) の充実はユーザー体験に直結する。
    -   **拡張性:** 新しいパターンやコマンドを容易に追加・修正できるよう、ルールや正規表現を外部ファイルや設定ファイルで管理することを検討する。コードの変更なしにパターンを追加できると理想的。
    -   **曖昧性処理:** パターンに一致しない場合や、複数の解釈が可能な場合に、ユーザーに確認を促すか、エラーメッセージを返すかの明確なルールを決めておく。
    -   **テスト:** 定義したパターンが意図通りに動作するか、多様な入力に対するテストケースを作成し、継続的に実行する。
-   **リリース後 (Agents SDK導入検討):**
    -   **移行計画:** パターン認識エンジンからAgents SDKへスムーズに移行するための計画を立てる。既存のパターン認識ロジックをツールとしてAgents SDKから呼び出す、段階的に機能を置き換える、などのアプローチが考えられる。
    -   **インターフェース:** 初期リリースのNLP Engineのインターフェース（入力と出力）を、将来的にAgents SDKに置き換えることを見越して設計しておく。
    -   **性能比較:** Agents SDK導入後に、パターン認識ベースの場合と比較して、応答精度、対応範囲、コスト（トークン使用量）、レイテンシなどを評価する。

## 7. プロジェクトファイル整理の指針

現在のプロジェクトルートには、過去の試行錯誤によるファイルや、新しい設計では不要になる可能性のあるファイルが含まれています。次回の開発サイクルを開始する前に、以下の指針に基づいて整理することを推奨します。

-   **削除/移動候補:**
    -   `.bak`, `.fixed`, `.new` などの拡張子を持つバックアップファイル。
    -   古いデータベースファイル (`app.db.*.bak`)。
    -   Alembic関連ファイル (`alembic.ini`, `alembic/`) - Firestore移行に伴い不要。
    -   古いデータベースモデルや接続関連コード (例: `src/models/database.py` 内のSQLAlchemy関連部分)。
    -   APScheduler関連のテストコードや設定。
    -   過去のデバッグ用スクリプトで、現在不要なもの (例: `debug_*.py`, `fix_*.py`, `test_*.py` の一部)。
    -   古いデプロイ関連ファイル/スクリプト (例: `create_deployment_package.ps1`, `create_zip.ps1`, `deployment_package.zip`) - Docker + Cloud Runベースに移行するため。
    -   複数の `.env` ファイル (`.env.production`, `.env.production.new`) - `.env` と `.env.example` に統一し、本番設定はSecret ManagerとCloud Run環境変数で管理。
    -   古いドキュメントやレポートで、最新の設計ドキュメント群に内容が吸収されたもの。
-   **推奨ディレクトリ構成 (再確認):** `SYSTEM_DESIGN_GCP.md` で提案されている構成 (`src/` 以下に `routers`, `services`, `repositories`, `models`, `nlp`, `core`, `utils` など) を基本とし、不要なディレクトリやファイルを整理します。
-   **`.gitignore` の確認:** 不要なファイル（`.env`, `venv*`, `__pycache__`, `*.pyc`, `*.log`, ローカルDBファイル等）が適切に除外されているか確認します。

## 8. 依存関係 (`requirements.txt`) の見直し

GCP Firestoreへの移行と初期リリースでのOpenAI Agents SDK見送りを踏まえ、`requirements.txt` を見直し、不要な依存関係を削除します。

-   **削除候補:**
    -   `sqlalchemy>=1.4.23`: Firestoreを使用するため不要。
    -   `openai-agents==0.0.9`: 初期リリースでは使用しない。 (将来拡張時に追加)
    -   `openai>=1.0.0,<2.0.0`: Agents SDKを使用しない場合、他のOpenAI API直接利用がなければ不要。
    -   `APScheduler>=3.9.1`: Cloud Tasks/Schedulerを使用するため不要。
    -   (その他) プロジェクトコード全体を確認し、`import` されていないライブラリがあれば削除を検討。
-   **バージョン固定:** CI/CDでの再現性を確保するため、`pip freeze > requirements.txt` などで、動作確認が取れた具体的なバージョンに固定することを推奨します。
-   **開発用依存関係:** `pytest`, `black`, `flake8` などは開発時にのみ必要です。本番のDockerイメージには含めないように、`requirements-dev.txt` などに分離するか、Dockerfileのマルチステージビルドを活用します。
