"""投稿画面（掲示板）の処理をまとめたファイル

いまはデータベースを使わず、このファイルの中にある
ダミーデータを表示しています。
あとで models/post.py（DB操作）に置きかえます。
"""

from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for

# この投稿機能のルートをひとまとめにする名前
# app.py で register_blueprint(post_bp) すると有効になります
post_bp = Blueprint("post", __name__)


# チャレンジルームの一覧
# あとで rooms テーブルから取ってくる予定の部分です
ROOMS = [
    {"id": "room_01", "name": "早起きチャレンジ"},
    {"id": "room_02", "name": "筋トレチャレンジ"},
    {"id": "room_03", "name": "読書チャレンジ"},
    {"id": "room_04", "name": "勉強チャレンジ"},
    {"id": "room_05", "name": "禁酒チャレンジ"},
]


# 投稿のダミーデータ
# ルームIDごとに、投稿のリストを持っています
# あとで posts テーブルから取ってくる予定の部分です
POSTS = {
    "room_01": [
        {
            "user_name": "山田太郎",
            "content": "今日は5時に起きられました！朝日がきれいです。",
            "created_at": "2026-07-26 05:12",
            "replies": ["すごい！わたしも頑張ります", "早起き仲間ですね"],
            "reactions": 3,
        },
        {
            "user_name": "鈴木二郎",
            "content": "6時起き達成。3日連続です。",
            "created_at": "2026-07-26 06:03",
            "replies": ["連続記録おめでとうございます"],
            "reactions": 5,
        },
    ],
    "room_02": [
        {
            "user_name": "佐藤三郎",
            "content": "腕立て30回やりました。",
            "created_at": "2026-07-26 21:40",
            "replies": [],
            "reactions": 2,
        },
    ],
    "room_03": [
        {
            "user_name": "田中四郎",
            "content": "今日は20ページ読みました。",
            "created_at": "2026-07-26 22:15",
            "replies": ["どんな本ですか？"],
            "reactions": 1,
        },
    ],
    "room_04": [],
    "room_05": [],
}


def find_room_name(room_id):
    """ルームIDから、そのルームの名前を探して返す"""
    for room in ROOMS:
        if room["id"] == room_id:
            return room["name"]
    return ""


@post_bp.route("/posts", methods=["GET"])
def posts_view():
    """掲示板ページを表示する

    アドレスの ?room_id=room_01 の部分を読み取って、
    そのルームの投稿だけを画面に渡します。
    """
    # プルダウンで選ばれたルームID
    # 指定がないときは、いちばん上のルームを表示します
    room_id = request.args.get("room_id", ROOMS[0]["id"])

    # そのルームの投稿を取り出す（無ければ空のリスト）
    posts = POSTS.get(room_id, [])

    return render_template(
        "post/posts.html",
        rooms=ROOMS,
        room_id=room_id,
        room_name=find_room_name(room_id),
        posts=posts,
    )


@post_bp.route("/posts", methods=["POST"])
def create_post():
    """投稿ボタンが押されたときの処理

    いまはデータベースではなく、上の POSTS に追加しています。
    （コンテナを再起動すると消えます）
    """
    room_id = request.form.get("room_id", ROOMS[0]["id"])
    content = request.form.get("content", "").strip()

    # 空の投稿は追加しない
    if content != "":
        new_post = {
            "user_name": "あなた",
            "content": content,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "replies": [],
            "reactions": 0,
        }
        # そのルームのリストの先頭に追加する（新しい順に並べるため）
        POSTS.setdefault(room_id, []).insert(0, new_post)

    # 投稿したあとは、同じルームの掲示板に戻る
    return redirect(url_for("post.posts_view", room_id=room_id))
