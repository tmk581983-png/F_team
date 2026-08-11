from flask import Blueprint, render_template, request, redirect,  url_for

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
        login_id = request.form["login_id"]
        user_name = request.form["user_name"]
        password = request.form["password"]

        #未入力の項目がないか確認する
        if not login_id or not user_name or not password:
            return render_template(
            "signup.html",
            error="すべての項目を入力してください"
        )

    #受け取れた値をDockerのログで確認する
        print(f"Login ID: {login_id}")
        print(f"User Name: {user_name}")
        print(f"Password: {password}")
        print("新規登録フォームが送信されました")


    #登録ボタンを押したらマイページへ移動する
        return redirect(url_for("mypage.index"))
    

#GETでもPOSTでも、最後に新規登録画面を表示する
    return render_template("signup.html")
