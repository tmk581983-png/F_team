from flask import Flask, redirect, url_for

# 投稿機能（掲示板）のまとまりを読み込む
from routes.post import post_bp

app = Flask(__name__)

# 投稿機能を、このアプリに登録する
app.register_blueprint(post_bp)


@app.route("/")
def index():
    # トップページに来たら、掲示板ページへ送る
    return redirect(url_for("post.posts_view"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
