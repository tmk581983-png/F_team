# base.html でレイアウトを統一する手順

## これは何をするものか

いま、各画面のHTMLがそれぞれ独立して書かれています。

```
login.html            ← <!DOCTYPE html> から全部書いている
challenge_room.html   ← <!DOCTYPE html> から全部書いている
posts.html            ← <!DOCTYPE html> から全部書いている
```

これを、共通部分を1ファイルにまとめた形に変えます。

```
base.html                    ← 共通部分（head・ヘッダー・フッター）はここだけ
├── auth/login.html          ← 中身だけ書く
├── room/challenge_room.html ← 中身だけ書く
└── post/posts.html          ← 中身だけ書く
```

## なぜやるのか

| いまの問題 | 統一後 |
|---|---|
| ヘッダーを直すのに3ファイル触る | base.html を1回直せば全画面に反映 |
| 画面ごとにフォントや色が微妙に違う | 自動でそろう |
| 同じ内容を3回書いている | 1回だけ |

---

## 変換手順（1画面あたり5分）

### 手順1：先頭に1行足す

ファイルの**いちばん上**に、これを書きます。

```html
{% extends "base.html" %}
```

### 手順2：共通部分を削除する

以下を**すべて削除**します。

- `<!DOCTYPE html>` から `<body>` までの全部
- 末尾の `</body>` と `</html>`

### 手順3：タイトルを block に入れる

削除した `<title>ログイン</title>` を、こう書き直します。

```html
{% block title %}ログイン{% endblock %}
```

### 手順4：この画面だけのCSSを block に入れる

削除した `<link rel="stylesheet" ...>` のうち、
**この画面だけで使うもの**を、こう書き直します。

```html
{% block page_css %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/login_style.css') }}">
{% endblock %}
```

### 手順5：残った中身を block content で挟む

```html
{% block content %}
　（元の <body> の中にあった内容をそのままここへ）
{% endblock %}
```

---

## 変換の前後（login.html の例）

### 変換前

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ログイン</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/login_style.css') }}">
</head>
<body>

  <div class="login-box">
    <h1>ログイン</h1>
    <form action="/" method="post">
      ...
    </form>
  </div>

</body>
</html>
```

### 変換後

```html
{% extends "base.html" %}

{% block title %}ログイン{% endblock %}

{% block page_css %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/login_style.css') }}">
{% endblock %}

{% block content %}

  <div class="login-box">
    <h1>ログイン</h1>
    <form action="/" method="post">
      ...
    </form>
  </div>

{% endblock %}
```

**中身（div から div まで）は1文字も変えていません。**
外側の包み方を変えただけです。

---

## CSSの分け方

| ファイル | 書くもの | 触る人 |
|---|---|---|
| `static/css/base.css` | 全画面共通（body・ヘッダー・フッター・.page） | 担当者1人だけ |
| `static/css/login_style.css` | ログイン画面だけ | ログイン担当 |
| `static/css/challenge.css` | ルーム画面だけ | ルーム担当 |
| `static/css/posts.css` | 投稿画面だけ | 投稿担当 |

### クラス名のルール（重要）

**クラス名の先頭に、画面がわかる言葉を付けてください。**

```css
.post-card     ← 投稿画面
.auth-form     ← ログイン画面
.room-list     ← ルーム画面
```

理由：同じクラス名を別の人が使うと、**Gitは何も警告しないのに画面だけ壊れます**。
原因が非常に見つけにくいバグになります。

```css
/* posts.css */
.card { background: white; }

/* login_style.css */
.card { background: gray; }   /* ← 後から読まれた方が勝つ */
```

---

## テンプレートの置き場所

機能ごとのフォルダに分けます。

```
app/templates/
├── base.html                    ← 共通（担当者1人だけが触る）
├── auth/
│   └── login.html
├── room/
│   └── challenge_room.html
└── post/
    └── posts.html
```

Python側の書き方も、フォルダを含めた形になります。

```python
return render_template("auth/login.html")
```

---

## base.html にある3つの「穴」

| 穴の名前 | 何を入れるか | 必須か |
|---|---|---|
| `title` | ブラウザのタブに出る名前 | 任意 |
| `page_css` | その画面だけのCSS | 任意 |
| `content` | 画面の中身 | **必須** |

`content` だけは必ず書いてください。書かないと画面が真っ白になります。

---

## つまずいたときの確認リスト

| 症状 | 原因 |
|---|---|
| 画面が真っ白 | `{% block content %}` を書き忘れ |
| CSSが効かない | `page_css` の中に書いていない／ファイル名が違う |
| ヘッダーが二重に出る | 元の `<body>` などを消し忘れ |
| `TemplateNotFound` | フォルダ名を含めていない（`post/posts.html`） |

---

## 担当と約束ごと

- `base.html` と `base.css` は **担当者1人だけ**が編集する
- 変更したいときは、事前にチームに共有する
- 各自は自分の画面のHTMLとCSSだけを触る

---

## 実際に動いている見本

`feature/post-form` ブランチに、この形で動く見本があります。

- `app/templates/base.html`
- `app/templates/post/posts.html`
- `app/static/css/base.css`
- `app/static/css/posts.css`
