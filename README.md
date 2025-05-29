# LINE Googleカレンダー連携 AIエージェント (GCP版)

## 1. プロジェクト概要

このプロジェクトは、LINEとGoogleカレンダーを連携させ、LINEのチャットインターフェースを通じて自然言語でスケジュール管理ができるAIエージェントを提供します。ユーザーはLINEから離れることなく、予定の追加、確認、変更、削除を行ったり、リマインダー通知を受け取ったりできます。

**目標:**
- LINEを通じたシームレスなスケジュール管理体験の提供
- 自然言語による直感的な操作性の実現
- GCP (Google Cloud Platform) を活用したスケーラブルで信頼性の高いサービスの構築

**主な機能:**
- LINEからのGoogleカレンダーへの予定追加・確認・変更・削除
- Googleカレンダーの予定に基づくLINEへのリマインダー通知
- 自然言語（日本語）による予定操作（初期リリースはパターン認識ベース、将来的にAI強化）
- LINE LIFFを用いたGoogleアカウント連携と設定管理

## 2. システムアーキテクチャ (GCP)

本システムはGCPのマネージドサービスを中心に構築されています。

- **実行環境:** Google Cloud Run (FastAPI / Python)
- **データベース:** Google Cloud Firestore
- **認証:** LINE Login, Google OAuth 2.0 (PKCE), LINE LIFF
- **非同期処理:** Google Cloud Tasks, Cloud Scheduler
- **機密情報管理:** Google Cloud Secret Manager
- **CI/CD:** GitHub Actions
- **監視:** Google Cloud Logging, Cloud Monitoring

詳細なアーキテクチャ図とコンポーネント設計は以下のドキュメントを参照してください。
- **[システム設計書 (GCP版)](./SYSTEM_DESIGN_GCP.md)**

## 3. 技術スタック

- **バックエンド:** Python 3.9+, FastAPI
- **データベース:** Firestore
- **フロントエンド (LIFF):** HTML, CSS, JavaScript
- **外部API/SDK:**
    - LINE Messaging API SDK (Python v3)
    - LINE LIFF SDK (JavaScript)
    - Google Calendar API v3 (google-api-python-client)
    - Google Authentication Library (google-auth-oauthlib)
    - (将来拡張) OpenAI Agents SDK
- **インフラ:** GCP (Cloud Run, Firestore, Tasks, Scheduler, Secret Manager, etc.)
- **CI/CD:** Docker, GitHub Actions

## 4. セットアップと実行

### 4.1 前提条件

- Python 3.9+
- Google Cloud SDK (gcloud CLI)
- Docker
- (推奨) `pyenv` や `conda` 等のPythonバージョン管理ツール
- (推奨) `ngrok` (ローカルでのWebhookテスト用)

### 4.2 環境設定

1.  **GCPプロジェクト設定:**
    - GCPプロジェクトを作成または選択。
    - 必要なAPI (Cloud Run, Firestore, Secret Manager, Cloud Tasks, Cloud Scheduler, Google Calendar API等) を有効化。
    - Cloud Run サービスアカウントに必要なIAM権限 (Secret Manager Secret Accessor, Firestore User, Cloud Tasks Enqueuer等) を付与。
2.  **LINE Developers設定:**
    - Messaging APIチャネルを作成（または既存のものを利用）。
    - チャネルアクセストークン（長期）とチャネルシークレットを取得。
    - Webhook URLを設定 (例: Cloud RunサービスのURL + `/webhook`)。
    - LIFFアプリを作成し、LIFF IDを取得。エンドポイントURLを設定 (例: Cloud RunサービスのURL + `/liff`)。
3.  **Google Cloud Console設定:**
    - OAuth 2.0 クライアントIDを作成（ウェブアプリケーションタイプ）。
    - クライアントIDとクライアントシークレットを取得。
    - 承認済みリダイレクトURIを設定 (例: Cloud RunサービスのURL + `/auth/google/callback`)。
4.  **Secret Manager設定:**
    - 以下のシークレットを作成し、対応する値を設定します。
        - `line-channel-secret`
        - `line-channel-access-token`
        - `google-client-id`
        - `google-client-secret`
        - `google-redirect-uri`
        - `google-refresh-token-encryption-key` (32バイトのURLセーフなBase64エンコードキーを生成: `python -c 'import os; print(os.urandom(32).hex())'`)
        - `openai-api-key` (将来拡張用)
5.  **ローカル環境設定:**
    - リポジトリをクローンします。
    - Python仮想環境を作成し、アクティベートします。
      ```bash
      python -m venv venv_py312 # 例
      source venv_py312/bin/activate # Linux/macOS
      # venv_py312\Scripts\activate # Windows
      ```
    - 依存関係をインストールします。
      ```bash
      pip install -r requirements.txt
      ```
    - `.env.example` をコピーして `.env` ファイルを作成し、ローカル開発用の設定（GCPプロジェクトID、Firestoreエミュレータ設定など）を記述します。**注意:** 機密情報は `.env` に直接記述せず、ローカルでのテスト用にgcloud認証 (`gcloud auth application-default login`) やエミュレータを使用することを推奨します。

### 4.3 ローカル実行 (Docker Compose推奨)

ローカルでの開発・テストにはDocker Composeを使用することを強く推奨します。これにより、Cloud Run環境に近い状態で実行できます。

1.  **Docker Composeファイルの準備:** (プロジェクトに `docker-compose.yml` がない場合は作成)
    - FastAPIアプリケーション、Firestoreエミュレータを含むサービスを定義します。
    - 環境変数を `.env` ファイルから読み込むように設定します。
2.  **起動:**
    ```bash
    docker-compose up -d --build
    ```
3.  **Webhookテスト (ngrok):**
    ```bash
    ngrok http 8000 # FastAPIコンテナが公開するポート
    ```
    表示されたngrokのURL (`https://xxxx.ngrok.io`) をLINE DevelopersコンソールのWebhook URLに設定します。

### 4.4 GCPへのデプロイ (CI/CD)

`main` ブランチへのマージをトリガーとして、GitHub Actionsによる自動デプロイが設定されています（詳細は `.github/workflows/deploy.yml` を参照）。

1.  コード変更をpushし、プルリクエストを作成・マージします。
2.  GitHub Actionsが自動的にテスト、ビルド、DockerイメージのArtifact Registryへのプッシュ、Cloud Runへのデプロイ（ステージング/本番）を実行します。

## 5. 主要ドキュメント

プロジェクトの詳細については、以下のドキュメントを参照してください。

-   **要件定義:** [カレンダーLINE連携要件定義.md](./カレンダーLINE連携要件定義.md)
-   **システム設計:** [SYSTEM_DESIGN_GCP.md](./SYSTEM_DESIGN_GCP.md)
-   **開発からの学び:** [LESSONS_LEARNED.md](./LESSONS_LEARNED.md)
-   **開発・運用メモ:** [DEVELOPMENT_NOTES.md](./DEVELOPMENT_NOTES.md)
-   **API実装ガイド:**
    -   [GoogleカレンダーAPI実装ガイド.txt](./GoogleカレンダーAPI実装ガイド.txt)
    -   [LINE連携 最新実装ガイド.txt](./LINE連携 最新実装ガイド.txt)
    -   [OpenAI agents SDK導入ガイド.txt](./OpenAI%20agents%20SDK導入ガイド.txt) (将来拡張向け)
-   **更新履歴:** [CHANGELOG.md](./CHANGELOG.md) (必要に応じて作成・更新)

## 6. ライセンス

MIT License
