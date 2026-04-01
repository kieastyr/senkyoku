# 🎼 選曲・提出システム (Senkyoku)

Python (Streamlit) ベースの選曲・提出管理システムです。
Google スプレッドシートと連携して、選曲データの提出とバリデーションを行います。

## 機能
- **メイン曲・サブ曲の選択**: 楽器構成や分数に基づいたリアルタイム・バリデーション。
- **動的フィルタリング**: 合計分数が100分を超えないサブ曲のみを自動で提示。
- **楽器構成チェック**: 全パート（フルート〜チューバ）に少なくとも1名の奏者が含まれているか確認。
- **Google Sheets 連携**: 提出された選曲データを Google スプレッドシートへ自動保存。
- **コメント表示**: 過去の提出者からのコメントをアプリ上で確認可能。

## セットアップ

### 1. 依存関係のインストール
`uv` を使用してインストールします。
```bash
uv sync
```

### 2. 環境設定
`.streamlit/secrets.toml` を作成し、Google スプレッドシートの接続情報を設定してください。
```toml
[connections.gsheets]
spreadsheet = "YOUR_SPREADSHEET_URL_OR_ID"
# サービスアカウントを使用する場合
type = "service_account"
...
```

### 3. 実行
```bash
uv run streamlit run main.py
```

## データソース
`datasource/` 配下の CSV ファイルを使用します。
- `main_list.csv`
- `sub_list.csv`
