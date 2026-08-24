from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_bcrypt import check_password_hash
from utils.db import get_connection

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
        #DBに接続する
        connection = get_connection()

        #入力されたlogin_idのユーザーを探す
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, login_id, password FROM users WHERE login_id = %s AND deleted_at IS NULL",
                (login_id,))
            
            user = cursor.fetchone()

        #DBとの接続を閉じる
        connection.close()

        

        #ユーザーが存在しない場合はエラーを返す
        if not user:
            return render_template("login.html", error="IDまたはパスワードが違います")

        #パスワードが一致するか確認する
        password_ok = check_password_hash(user["password"], password)


        #passwordが一致しない場合はエラーを返す
        if not password_ok:
            return render_template("login.html", error="IDまたはパスワードが違います")

        #ログインしたユーザーのIDをセッションに保存する
        session["user_id"] = user["id"]

        #ログインボタンを押したらマイページへ移動する
        return redirect(url_for("mypage.index"))

    #GETのときはログイン画面を表示する
    return render_template("login.html")


