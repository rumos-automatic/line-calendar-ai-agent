# 🤖 LINE Google Calendar AI Agent

LINEとGoogleカレンダーを連携させ、自然言語でスケジュール管理ができるAIエージェントです。

## ✨ 特徴

### 🤖 AIエージェント機能
- **自然な会話**: 「来週忙しいかな？」「さっきの会議キャンセルして」
- **文脈理解**: 前の会話を覚えて「その予定」「さっきの」を理解
- **プロアクティブ提案**: 忙しい日の休憩提案、早朝会議前の早寝提案

### 📅 カレンダー操作
- **予定追加**: 「明日の15時に会議」
- **予定確認**: 「今日の予定は？」「来週の金曜日は？」
- **予定削除**: 「明日の会議キャンセル」
- **リマインダー**: カスタマイズ可能な通知設定

### 💳 課金プラン対応
- **無料プラン**: パターン認識モード + AI月10回
- **ベーシックプラン**: AIモード月100回（500円/月）
- **プレミアムプラン**: AIモード無制限（1,500円/月）

## 🚀 技術スタック

### バックエンド
- **Python** + **FastAPI**
- **OpenAI GPT-4** (Function Calling)
- **Google Firestore** (NoSQL Database)
- **Vercel** (Serverless Functions)

### 外部連携
- **LINE Messaging API** + **LIFF**
- **Google Calendar API**
- **Google OAuth 2.0** (PKCE)

### AI機能
- **OpenAI Function Calling** によるツール実行
- **会話履歴管理** による文脈理解
- **日本語特化NLP** (パターン認識 + AI)

## 📦 デプロイ

### Vercelデプロイ
```bash
# 1. リポジトリをクローン
git clone https://github.com/your-username/line-calendar-ai-agent.git

# 2. Vercelにデプロイ
vercel --prod

# 3. 環境変数を設定
# Vercelダッシュボードで必要な環境変数を設定
```

詳細は [`VERCEL_DEPLOY.md`](./VERCEL_DEPLOY.md) を参照。

## 🔧 ローカル開発

```bash
# 1. 依存関係インストール
pip install -r requirements.txt

# 2. 環境変数設定
cp .env.example .env
# .envファイルを編集

# 3. Docker Composeで起動
docker-compose up --build
```

## 📖 ドキュメント

- **[Vercelデプロイ手順](./VERCEL_DEPLOY.md)** - 本番環境構築
- **[システム設計](./SYSTEM_DESIGN_GCP.md)** - アーキテクチャ詳細
- **[要件定義](./カレンダーLINE連携要件定義.md)** - 機能仕様
- **[開発メモ](./DEVELOPMENT_NOTES.md)** - 技術的な注意点

## 🤝 使い方

### 1. 友だち追加
LINE Bot を友だち追加

### 2. Google連携
LIFF画面でGoogleアカウントを連携

### 3. 自然な会話
```
ユーザー: 「来週忙しいかな？」
AI: 「来週は5件の予定があります。特に水曜日は会議が3つ重なっていて忙しそうですね。」

ユーザー: 「水曜の午後の会議キャンセルして」
AI: 「水曜日15:00からの『企画会議』をキャンセルしました。」
```

## 📊 プラン比較

| プラン | 料金 | AIモード | 月間AI利用 |
|--------|------|----------|------------|
| 無料 | 0円 | ❌ | 10回 |
| ベーシック | 500円 | ✅ | 100回 |
| プレミアム | 1,500円 | ✅ | 無制限 |

## 🛠️ 開発者向け

### AI Function Tools
- `search_events` - 予定検索
- `add_event` - 予定追加
- `delete_event` - 予定削除
- `update_reminder_settings` - リマインダー設定
- `check_subscription` - プラン確認
- `upgrade_subscription` - プランアップグレード

### API エンドポイント
- `POST /webhook` - LINE Webhook
- `GET /liff/*` - LIFF API
- `GET /auth/google/callback` - OAuth コールバック
- `GET /health` - ヘルスチェック

## 📄 ライセンス

MIT License

## 🙋‍♂️ サポート

質問や要望は Issues でお気軽にどうぞ！