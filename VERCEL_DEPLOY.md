# Vercel デプロイ手順

## 🚀 Vercel へのデプロイ

### 1. 前準備

#### 1.1 Google Cloud Platform 設定
```bash
# 1. GCPプロジェクト作成（まだの場合）
gcloud projects create your-project-id

# 2. Firestore データベース作成
gcloud firestore databases create --region=asia-northeast1

# 3. サービスアカウント作成
gcloud iam service-accounts create line-calendar-bot \
  --display-name="LINE Calendar Bot"

# 4. サービスアカウントに権限付与
gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:line-calendar-bot@your-project-id.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

# 5. サービスアカウントキー作成
gcloud iam service-accounts keys create service-account-key.json \
  --iam-account=line-calendar-bot@your-project-id.iam.gserviceaccount.com
```

#### 1.2 LINE Developers 設定
1. **Messaging API チャネル作成**
   - チャネルアクセストークン（長期）を取得
   - チャネルシークレットを取得

2. **LIFF アプリ作成**
   - エンドポイントURL: `https://your-app.vercel.app/liff`
   - サイズ: Full
   - LIFF ID を取得

#### 1.3 Google OAuth 設定
1. **OAuth 2.0 クライアント ID 作成**
   - アプリケーションの種類: ウェブアプリケーション
   - 承認済みのリダイレクト URI: `https://your-app.vercel.app/auth/google/callback`

### 2. Vercel デプロイ

#### 2.1 Vercel CLI インストール
```bash
npm install -g vercel
```

#### 2.2 プロジェクトをアップロード
```bash
# GitHubにプッシュ
git add .
git commit -m "Vercel ready"
git push origin main
```

#### 2.3 Vercel ダッシュボードで設定

1. **プロジェクト作成**
   - GitHub リポジトリを接続
   - Framework Preset: "Other"

2. **環境変数設定**
   
   以下の環境変数を Vercel ダッシュボードの Environment Variables で設定：

   ```
   GOOGLE_CLOUD_PROJECT=your-gcp-project-id
   GOOGLE_SERVICE_ACCOUNT_KEY={"type":"service_account","project_id":"..."}
   ENVIRONMENT=production
   RUNTIME=vercel
   USE_AI_AGENT=true
   
   LINE_CHANNEL_SECRET=your-line-channel-secret
   LINE_CHANNEL_ACCESS_TOKEN=your-line-channel-access-token
   LIFF_ID=your-liff-id
   
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GOOGLE_REDIRECT_URI=https://your-app.vercel.app/auth/google/callback
   
   OPENAI_API_KEY=your-openai-api-key
   ENCRYPTION_KEY=ランダムな32文字の文字列
   BASE_URL=https://your-app.vercel.app
   ```

   **重要**: `GOOGLE_SERVICE_ACCOUNT_KEY` には `service-account-key.json` の全内容を文字列として貼り付け

#### 2.4 デプロイ実行
```bash
vercel --prod
```

### 3. 設定の更新

#### 3.1 LINE Webhook URL更新
```
Webhook URL: https://your-app.vercel.app/webhook
```

#### 3.2 LIFF エンドポイント URL更新
```
エンドポイントURL: https://your-app.vercel.app/liff
```

#### 3.3 Google OAuth リダイレクト URI更新
```
承認済みのリダイレクト URI: https://your-app.vercel.app/auth/google/callback
```

### 4. 動作確認

#### 4.1 基本チェック
```bash
# ヘルスチェック
curl https://your-app.vercel.app/health

# レスポンス例
{"status":"healthy","runtime":"vercel"}
```

#### 4.2 LINE Bot テスト
1. LINE Bot を友だち追加
2. メッセージ送信テスト：
   ```
   「明日の15時に会議」
   「今日の予定は？」
   「プラン確認」
   ```

#### 4.3 Google 連携テスト
1. LIFF アプリを開く
2. Google アカウント連携を実行
3. 連携完了を確認

### 5. トラブルシューティング

#### 5.1 よくあるエラー

**Function timeout**
```
Solution: Vercel の Function timeout は 10秒（Hobby plan）
長時間処理は分割するか、Pro plan にアップグレード
```

**Firestore connection error**
```
Solution: GOOGLE_SERVICE_ACCOUNT_KEY の JSON が正しく設定されているか確認
```

**LINE signature verification failed**
```
Solution: LINE_CHANNEL_SECRET が正しく設定されているか確認
```

#### 5.2 ログ確認
```bash
# Vercel ログ確認
vercel logs https://your-app.vercel.app

# または Vercel ダッシュボードの Functions タブで確認
```

### 6. 本番運用

#### 6.1 監視設定
- Vercel Analytics を有効化
- エラー通知設定
- パフォーマンス監視

#### 6.2 スケーリング
- Pro plan でより高いリクエスト制限
- Edge Functions での高速化検討

#### 6.3 セキュリティ
- 環境変数の定期的な更新
- アクセスログの監視

## 🎉 完了！

これで Vercel での運用が開始されます。ngrok よりもずっと簡単で安定した環境が手に入りました！