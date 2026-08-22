from flask import Blueprint, render_template, session, request, redirect, url_for
from models.room_list import (
    get_room_lists,
    create_room_participation,
)
from models.mypage import get_joined_room

room_list_bp = Blueprint("room_list", __name__, url_prefix="/room_list")


@room_list_bp.route("/", methods=["GET"])
def index():
    """チャレンジルーム一覧を取得する"""
    user_id = session.get("user_id")

    if user_id is None:
        return redirect(url_for("login.login"))

    rooms = get_room_lists()

    return render_template("room_list.html", rooms=rooms)


@room_list_bp.route("/register", methods=["POST"])
def register():
    """ルーム参加処理を行う"""
    user_id = session.get("user_id")

    if user_id is None:
        return redirect(url_for("login.login"))

    # 直接アクセスによる複数ルーム参加を防止
    joined_room = get_joined_room(user_id)

    if joined_room:
        return redirect(url_for("mypage.index"))

    room_id = int(request.form["room_id"])

    create_room_participation(user_id, room_id)

    return redirect(url_for("challenge.room", room_id=room_id))
