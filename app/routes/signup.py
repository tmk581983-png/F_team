from flask import Blueprint, render_template, request, redirect,  url_for, session
from flask_bcrypt import generate_password_hash
from utils.db import get_connection

#新規登録画面用のBlueprint
signup_bp = Blueprint(
    "signup",
    __name__,
    url_prefix="/signup"

)

# /signup/へのGETとPOSTを受け付ける
@signup_bp.route("/", methods=["GET", "POST"])
def index():

    #登録ボタンが押されて、POST送信されたときだけ実行する
    if request.method == "POST":

        #HTMLのname属性を使って入力値を受け取る
        login_id = request.form["login_id"].strip()
        user_name = request.form["user_name"].strip()
        password = request.form["password"]

        #未入力の項目がないか確認する
        if not login_id or not user_name or not password:
            return render_template(
            "signup.html",
            error="すべての項目を入力してください"
        )

        #DBに接続する
        connection = get_connection()

        #同じlogin_idがすでに登録されていないか確認する
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM users WHERE login_id = %s" ,
                (login_id,)
            )
            existing_user = cursor.fetchone()

        #DBとの接続を閉じる
        connection.close()

        #同じlogin_idが見つかった場合
        if existing_user:
            return render_template(
                "signup.html",
                error="このIDはすでに使われています"
            )

        #パスワードをハッシュ化する
        hashed_password = generate_password_hash(password).decode("utf-8")

        #新しいユーザーをusersテーブルに登録する
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (name, login_id, password)
                VALUES (%s, %s, %s)
                """,
                (user_name, login_id, hashed_password)

            )

            #今登録したユーザーのIDを取得する
            user_id = cursor.lastrowid


        connection.commit()
        connection.close()

        #登録したユーザーのIDをsessionに保存する
        session["user_id"] = user_id


        #登録ボタンを押したらマイページへ移動する
        return redirect(url_for("mypage.index"))
    

#GETでもPOSTでも、最後に新規登録画面を表示する
    return render_template("signup.html")
