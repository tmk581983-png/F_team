"""
投稿画面の処理

【R8.8.16 更新】
postsテーブルへDB接続
一覧の取得・投稿・削除・編集はmodels/post.py経由
チャレンジルームの一覧もroomsテーブルから取得するようにした。

【処理の流れ】
ブラウザ → 本ファイル →（models/post.py 経由でDBを読み書き）→ templates/posts.html → ブラウザ表示
"""

#   Blueprint      … アプリを分割して管理する仕組み
#   render_template… flaskモジュールのFlaskクラスとrender_template関数。HTMLファイルに値を差し込んで表示
#   request        … ブラウザから送られてきた値（リクエスト）
#   redirect       … 別のページへ移動
#   url_for        … エンドポイントのURLを利用
from flask import Blueprint, render_template, request, redirect, url_for

from models.post import (
    get_posts_view_data,
    get_joined_room_id,
    has_posted_today,
    update_streak_and_check_graduation,
    create_reply,
    toggle_reaction,
    create_post as db_create_post,
    delete_post as db_delete_post,
    update_post as db_update_post,
)


# ============================================================
# Blueprintをインポート
# ============================================================
post_bp = Blueprint("post", __name__)

# ログイン機能が未実装のため、仮のログインID。
# session["user_id"] が使えるようになったら、この行ごと削除して
# session.get("user_id") に置きかえる
CURRENT_USER_ID = 1

# リアクションの種類
REACTION_TYPES = [
    {"type": 1, "label": "応援！",   "emoji": "👏"},
    {"type": 2, "label": "すごい！", "emoji": "🎉"},
    {"type": 3, "label": "共感！",   "emoji": "🤝"},
]


# ============================================================
# 補助の関数（画面の処理から呼び出す）
# ============================================================

def find_room_name(rooms, room_id):
    """ルームIDから、ルーム名を探して返す
    見つからなかったときは、空の文字 "" を返す

    roomsはget_posts_view_data()で取ってきた一覧
    DBを2回見に行かないように取得済みの一覧を渡してもらうようにしている。
    """
    # rooms のリストを、上から1行ずつ見る
    for room in rooms:
        # IDが一致したら、ルーム名を返して終了
        if room["id"] == room_id:
            return room["name"]
    # 最後まで見つからなかった場合
    return ""


def to_view_posts(rows, reactions, replies):
    """
    rows：get_posts_view_data() で取得した投稿
    reactions：get_posts_view_data() で取得したリアクション
    replies：get_posts_view_data() で取得した返信

    【処理】
    1. created_at（datetime型）を「YYYY-MM-DD HH:MM」に直す
    2. is_mine（自分の投稿かどうか）を追加
    3. リアクション、種類ごとの件数
    4. 投稿IDごとに返信をまとめる
    """

    reaction_map = {}
    for row in reactions:
        reaction_map.setdefault(row["post_id"], {})[row["reaction_type"]] = {
            "count": row["count"],
            "mine": int(row["mine"] or 0) > 0,
        }

    # 返信を、投稿IDごとにまとめる
    reply_map = {}
    for row in replies:
        reply_map.setdefault(row["parent_post_id"], []).append({
            "user_name": row["user_name"],
            "content": row["content"],
            "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M"),
        })

    posts = []
    for row in rows:
        post_id = row["id"]

        # この投稿のリアクションを、種類ごとにする
        reactions_view = []
        for rt in REACTION_TYPES:
            data = reaction_map.get(post_id, {}).get(rt["type"])
            reactions_view.append({
                "type": rt["type"],
                "label": rt["label"],
                "emoji": rt["emoji"],
                "count": data["count"] if data else 0,
                # 自分が押しているか（色を変える）
                "active": data["mine"] if data else False,
            })

        posts.append({
            "id": post_id,
            "user_name": row["user_name"],
            "content": row["content"],
            "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M"),
            "is_mine": row["user_id"] == CURRENT_USER_ID,
            "reactions": reactions_view,
            "replies": reply_map.get(post_id, []),
        })
    return posts


# ============================================================
# 画面の処理（本体）
# ============================================================
@post_bp.route("/posts", methods=["GET"])
def posts_view():
    #ブラウザで/postsを開いたとき（GET）に投稿ページを表示

    # どのルームを見たいのか、指定があれば先に受け取る
    # アドレスの「?room_id=1」の部分を読み取り
    # type=int を付けると、文字の1ではなく数値の1で受け取れる
    room_id = request.args.get("room_id", type=int)

    # ルーム一覧・投稿・リアクション・返信を、1回の接続でまとめて取得
    # room_id がNoneの場合、投稿は取得されない
    rooms, post_rows, reaction_rows, reply_rows = get_posts_view_data(CURRENT_USER_ID, room_id)

    # 定が無かった場合は、いちばん上のルームを表示
    # このときはroom_idで問い合わせし直す
    # ルームが1件も無いときはNoneのままにして、下でDBを引かないようにする
    if room_id is None:
        room_id = rooms[0]["id"] if rooms else None
        if room_id is not None:
            rooms, post_rows, reaction_rows, reply_rows = get_posts_view_data(CURRENT_USER_ID, room_id)

    posts = to_view_posts(post_rows, reaction_rows, reply_rows)

    # 編集中の投稿があるか
    edit_id = request.args.get("edit_id", type=int)

    # 登録ルームの確認、投稿できるか、マイページへ戻れるか
    joined_room_id = get_joined_room_id(CURRENT_USER_ID)

    # 登録中のルームを見ているときだけ、投稿フォームを表示
    # リアクションは対象外（登録ルーム以外でも応援はできる）。
    can_post = (room_id is not None and room_id == joined_room_id)

    # 「マイページへ戻る」ボタンを押せるか判定
    # 登録ルームが無い（卒業直後など）ときは、妨げないようにする。
    # ここを False にすると、投稿もできずマイページにも戻れない。詰む
    # 登録ルームがあるときは、今日すでに投稿しているかで判定
    if joined_room_id is None:
        posted = True
    else:
        posted = has_posted_today(CURRENT_USER_ID, joined_room_id)

    # 卒業ポップアップを出すか
    # create_post() が、3日連続を達成した投稿のときだけgraduated=1
    just_graduated = request.args.get("graduated") == "1"

    # HTMLに値を渡して、画面作成
    return render_template(
        "posts.html",
        rooms=rooms,                               # プルダウンのルーム一覧
        room_id=room_id,                           # 選択されているルームID
        room_name=find_room_name(rooms, room_id),  # 選択されているルーム名
        posts=posts,                        # 投稿画面に表示する投稿
        posted=posted,                      # 投稿ボタンを押下後
        edit_id=edit_id,                    # 編集中の投稿ID
        can_post=can_post,                  # 選択中のルームに投稿できるか判定
        just_graduated=just_graduated,      # 卒業ポップアップ判定
    )


@post_bp.route("/posts", methods=["POST"])
def create_post():
    """投稿ボタンを押したとき
    【処理】
    1. 投稿フォームに入力された内容を受け取る
    2. DBのpostsテーブルに保存
    3. 投稿画面に戻る
    """

    # request.formは「フォームから送られてきた値」を受け取る
    # どのルームへの投稿かは、HTMLのhidden項目
    # フォームの値は必ず文字で届くので、type=intで数値にして受け取る
    room_id = request.form.get("room_id", type=int)

    # 登録中のルーム以外への投稿は受け付けない。
    # 画面側でフォームを隠しているが、直接POSTを送られたときに防げないため、ここでも確認
    if room_id != get_joined_room_id(CURRENT_USER_ID):
        return redirect(url_for("post.posts_view", room_id=room_id))

    # .strip()で前後の余分な空白や改行を取り除く
    content = request.form.get("content", "").strip()

    # 空・スペースだけの投稿はDBに保存しない
    graduated = False
    if content != "" and room_id is not None:
        db_create_post(CURRENT_USER_ID, room_id, content)
        # 投稿したときだけ、連続日数の判定
        graduated = update_streak_and_check_graduation(CURRENT_USER_ID, room_id)

    # 投稿画面に戻る（卒業したらgraduated=1でポップアップ表示）
    return redirect(
        url_for("post.posts_view", room_id=room_id, graduated=1 if graduated else None)
    )


@post_bp.route("/posts/<int:post_id>/delete", methods=["POST"])
def delete_post(post_id):
    """削除ボタンが押されたとき（POST）の処理
    【処理内容】
    1. どのルームの投稿を削除するのか特定
    2. DB側で「自分の投稿かどうか」を確認しつつ削除（models/post.py）
    3. 投稿画面に戻る
    ※ 自分の投稿でなければ、models側のWHERE条件に一致しないため、
       何も削除されずに終わる。アドレスを直接打たれても安全。
    """

    # どのルームか受け取る（戻り先の画面を決めるため）
    room_id = request.form.get("room_id", type=int)

    db_delete_post(post_id, CURRENT_USER_ID)

    # 投稿画面に戻る
    return redirect(url_for("post.posts_view", room_id=room_id))

@post_bp.route("/posts/<int:post_id>/edit", methods=["POST"])
def edit_post(post_id):
    """「保存する」ボタンが押されたとき（POST）の処理
    【処理内容】
    1. どのルームの投稿を編集するのか特定
    2. DB側で「自分の投稿かどうか」を確認しつつ書きかえる（models/post.py内）
    3. 投稿画面に戻る（編集フォームは閉じる）
    """

    # どのルームか（戻り先）
    room_id = request.form.get("room_id", type=int)

    # 書きかえ後の本文を受け取る
    new_content = request.form.get("content", "").strip()

    # 空の内容で保存されるのを防ぐ
    if new_content != "":
        db_update_post(post_id, CURRENT_USER_ID, new_content)

    # 投稿画面に戻る
    return redirect(url_for("post.posts_view", room_id=room_id))


@post_bp.route("/posts/<int:post_id>/reaction", methods=["POST"])
def react(post_id):
    """リアクションボタンが押されたとき（POST）の処理
    すでに押していれば取り消し、押していなければ登録
    自分の投稿には押せない、という確認はmodels側で行っている
    リアクションは、登録していないチャレンジルームでも可能。
    """
    room_id = request.form.get("room_id", type=int)
    reaction_type = request.form.get("reaction_type", type=int)

    # 想定外の番号のときは、何もしない
    valid_types = [rt["type"] for rt in REACTION_TYPES]
    if reaction_type in valid_types:
        toggle_reaction(CURRENT_USER_ID, post_id, reaction_type)

    # 投稿画面に戻る
    return redirect(url_for("post.posts_view", room_id=room_id))


@post_bp.route("/posts/<int:post_id>/reply", methods=["POST"])
def reply_post(post_id):
    # 返信ボタンが押されたとき（POST）の処理
    room_id = request.form.get("room_id", type=int)
    content = request.form.get("content", "").strip()

    if content != "" and room_id is not None:
        create_reply(CURRENT_USER_ID, room_id, post_id, content)

    return redirect(url_for("post.posts_view", room_id=room_id))
