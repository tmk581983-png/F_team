from flask import Blueprint, render_template, request, redirect, url_for

login_bp = Blueprint("login", __name__, url_prefix="/login")

@login_bp.route("/", methods=["GET", "POST"])
def login():

    #ログインボタンが押されて、POST送信されたときだけ実行する
    if request.method == "POST":

        #HTMLのname属性を使って入力値を受け取る
        login_id = request.form["user_id"].strip()
        password = request.form["password"]

        #未入力の項目がないか確認する
        if not login_id or not password:
            return render_template("login.html",error="IDとパスワードを入力してください")
        

        #受け取れた値をDockerのログで確認する
        print(f"Login ID: {login_id}")
        print(f"Password: {password}")
        print("ログインフォームが送信されました")

        #ログインボタンを押したらマイページへ移動する
        return redirect(url_for("mypage.index"))

    #GETのときはログイン画面を表示する
    return render_template("login.html")


