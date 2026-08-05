from flask import Blueprint, render_template, request, redirect, url_for

room_list_bp = Blueprint("room_list", __name__, url_prefix="/room_list")


@room_list_bp.route("/", methods=["GET"])
def index():

    # TODO: DBから取得したルーム一覧に置き換える
    rooms = [
        {"id": "1", "name": "目指せ！150ステップクリア！", "member_count": "10"},
        {"id": "2", "name": "ネットワークわけわからん", "member_count": "5"},
        {"id": "3", "name": "Linuxコマンド乱れ打ち", "member_count": "8"},
        {"id": "4", "name": "言語化してみる", "member_count": "3"},
        {"id": "5", "name": "一休み一休み", "member_count": "7"},
    ]

    return render_template(
        "room_list.html",
        rooms=rooms,
    )


@room_list_bp.route("/register", methods=["POST"])
def register():
    room_id = int(request.form["room_id"])

    # TODO: room_participationsへuser_idとroom_idを保存する

    return redirect(url_for("mypage.index"))
