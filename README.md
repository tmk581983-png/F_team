# F_team
2026夏ハッカソン

## 環境構築

### 1. 環境変数の設定

`.env.example` をコピーして `.env` を作成してください。

```
cp .env.example .env
```

作成後、`.env` の変更が必要な項目を任意の値に変更してください。

### 2. Dockerコンテナの起動

初回起動時やDocker関連の設定変更後は、以下を実行してください。

```
docker compose up -d --build
```

通常起動の場合は、以下を実行してください。

```
docker compose up -d
```

## アクセス方法

コンテナ起動後、以下のURLにアクセスしてください。

`http://localhost:55000`

## Dockerコンテナの停止

起動したコンテナを停止する場合は、以下を実行してください。

```
docker compose down
```

## ディレクトリ構成

```
.
├── app                       # Flaskアプリケーション
│   ├── app.py                # Flask起動ファイル
│   ├── routes/               # ルーティング処理
│   ├── models/               # データベースモデル
│   ├── templates/            # HTMLテンプレート
│   ├── static/               # 静的ファイル
│   │   ├── css/              # CSSファイル
│   │   ├── js/               # JavaScriptファイル
│   │   ├── images/           # アプリで使用する画像
│   │   └── uploads/          # ユーザーアップロードファイルの保存先
│   └── utils/                # 共通処理
│       └── db.py             # データベース接続処理
├── docs/                     # 開発ドキュメント
├── Docker                    # Docker設定
│   ├── Flask/                # Flaskコンテナ設定
│   │   └── Dockerfile        # Flaskコンテナの設定ファイル
│   └── MySQL/                # MySQLコンテナ設定
│       ├── Dockerfile        # MySQLコンテナの設定ファイル
│       ├── init.sql          # データベースの初期設定
│       └── my.cnf            # MySQLの設定ファイル
├── docker-compose.yml        # コンテナ構成設定
├── requirements.txt          # Pythonライブラリ一覧
└── .env.example              # 環境変数設定例
```