from flask import Blueprint, render_template, request, redirect, url_for

login_bp = Blueprint("login", __name__, url_prefix="/login")

@login_bp.route("/", methods=["GET", "POST"])
def login():

    #ログインボタンが押されて、POST送信されたときだけ実行する
    if request.method == "POST":

        #HTMLのname属性を使って入力値を受け取る
        login_id = request.form["user_id"]
        password = request.form["password"]

        #受け取れた値をDockerのログで確認する
        print(f"Login ID: {login_id}")
        print(f"Password: {password}")
        print("ログインフォームが送信されました")

        #ログインボタンを押したらマイページへ移動する
        return redirect(url_for("mypage.index"))

    #GETのときはログイン画面を表示する
    return render_template("login.html")


