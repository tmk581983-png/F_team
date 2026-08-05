from flask import Blueprint, render_template

mypage_bp = Blueprint("mypage", __name__, url_prefix="/mypage")


@mypage_bp.route("/")
def index():

    # TODO: user_idをもとに参加中のルーム情報をDBから取得する
    joined_room = {
        "id": "room_01",
        "name": "目指せ！150ステップクリア！",
        "member_count": 10,
    }

    return render_template(
        "mypage.html",
        name="RareTECHたける@33期生",
        achievement_count=5,
        joined_room=joined_room,
    )
