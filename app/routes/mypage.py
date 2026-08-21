from datetime import datetime, timedelta
from flask import Blueprint, render_template, session, request, redirect, url_for
from models.mypage import (
    get_mypage_user,
    update_mypage_user,
    get_achievement_count,
    get_posted_days,
    get_joined_room,
)

mypage_bp = Blueprint("mypage", __name__, url_prefix="/mypage")


@mypage_bp.route("/", methods=["GET"])
def index():
    """マイページを表示する"""
    user_id = session.get("user_id")

    if user_id is None:
        return redirect(url_for("login.login"))

    user = get_mypage_user(user_id)
    achievement_data = get_achievement_count(user_id)
    posted_days = get_posted_days(user_id)
    activity_data = create_activity_data(posted_days)
    joined_room = get_joined_room(user_id)

    return render_template(
        "mypage.html",
        user=user,
        achievement_data=achievement_data,
        activity_data=activity_data,
        joined_room=joined_room,
    )


@mypage_bp.route("/update", methods=["POST"])
def update():
    """プロフィール情報を更新する"""
    user_id = session.get("user_id")

    if user_id is None:
        return redirect(url_for("login.login"))

    name = request.form["name"]

    update_mypage_user(user_id, name)

    return redirect(url_for("mypage.index"))


@mypage_bp.route("/logout", methods=["POST"])
def logout():
    """ログイン情報を破棄してログアウトする"""
    session.clear()

    return redirect(url_for("login.login"))


def create_activity_data(posted_days):
    """過去30日間の活動状況を作成する"""
    # 投稿した日を取得
    posted_dates = {day["posted_date"] for day in posted_days}
    # 午前3時を日付の境界として今日の日付を取得
    today = (datetime.now() - timedelta(hours=3)).date()

    activity_data = []
    streak = 0

    # 今日を含む過去30日分を作成
    for i in range(30):
        current_date = today - timedelta(days=29 - i)

        if current_date in posted_dates:
            streak += 1

            if streak >= 3:
                status = "streak-3"
            elif streak >= 2:
                status = "streak-2"
            else:
                status = "streak-1"
        else:
            streak = 0
            status = "none"

        activity_data.append({"date": current_date, "status": status})

    return activity_data
