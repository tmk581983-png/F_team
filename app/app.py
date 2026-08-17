import os

from flask import Flask, redirect, session, url_for
from routes.login import login_bp
from routes.signup import signup_bp
from routes.room_list import room_list_bp
from routes.challenge import challenge_bp
from routes.mypage import mypage_bp
from routes.post import post_bp

app = Flask(__name__)

# セッション（ログイン状態の保持）に使う秘密鍵
# これを設定しないと session に値を書き込んだ瞬間にエラーになる
app.secret_key = os.getenv("SECRET_KEY")

# Blueprint登録
app.register_blueprint(login_bp)
app.register_blueprint(signup_bp)
app.register_blueprint(room_list_bp)
app.register_blueprint(challenge_bp)
app.register_blueprint(mypage_bp)
app.register_blueprint(post_bp)


@app.route("/", methods=["GET"])
def index():
    if "user_id" in session:
        return redirect(url_for("mypage.index"))

    return redirect(url_for("login.login"))



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
