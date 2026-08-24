"""
投稿画面の処理

【R8.8.16】
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
import os
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, current_app

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

# 添付画像として許可する拡張子
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def save_image(file):
    """アップロードされた画像をstatic/uploadsに保存し、保存したファイル名を返す
    画像が選択されていない、または対象外の拡張子のときはNoneを返す

    ファイル名はそのまま使わずランダムな名前に変更している
    （他人のファイル名との衝突・上書き事故を防ぐため）
    """
    if file is None or file.filename == "":
        return None

    if "." not in file.filename:
        return None

    ext = file.filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return None

    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = os.path.join(current_app.static_folder, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))
    return filename


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


def to_view_posts(user_id, rows, reactions, replies):
    """
    user_id：今ログインしているユーザーのID（is_mineの判定に使う）
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
            "id": row["id"],
            "user_name": row["user_name"],
            "content": row["content"],
            "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M"),
            "is_mine": row["user_id"] == user_id,
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
            "image_path": row["image_path"],
            "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M"),
            "is_mine": row["user_id"] == user_id,
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
    user_id = CURRENT_USER_ID

    # どのルームを見たいのか、指定があれば先に受け取る
    # アドレスの「?room_id=1」の部分を読み取り
    # type=int を付けると、文字の1ではなく数値の1で受け取れる
    room_id = request.args.get("room_id", type=int)

    # 【変更】room_id未指定時にどのルームを表示するか判定するため、
    # 登録ルームの確認をここに前倒しした（元は下の方で取得していた）
    joined_room_id = get_joined_room_id(user_id)

    # ルーム一覧・投稿・リアクション・返信を、1回の接続でまとめて取得
    # room_id がNoneの場合、投稿は取得されない
    rooms, post_rows, reaction_rows, reply_rows = get_posts_view_data(user_id, room_id)

    # 指定が無かった場合の表示先を決める
    # 【変更】challenge_room画面などroom_idを付けずに遷移してきたとき、
    # 以前は常に「一覧の先頭のルーム」を表示していたが、
    # それだと自分の登録ルームと違うルームが表示されることがあったため、
    # 登録中のルームがあればそれを優先して表示するようにした
    # ルームが1件も無いときはNoneのままにして、下でDBを引かないようにする
    if room_id is None:
        room_id = joined_room_id if joined_room_id is not None else (rooms[0]["id"] if rooms else None)
        if room_id is not None:
            rooms, post_rows, reaction_rows, reply_rows = get_posts_view_data(user_id, room_id)

    posts = to_view_posts(user_id, post_rows, reaction_rows, reply_rows)

    # 編集中の投稿があるか
    edit_id = request.args.get("edit_id", type=int)

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
        posted = has_posted_today(user_id, joined_room_id)

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
    user_id = CURRENT_USER_ID

    # request.formは「フォームから送られてきた値」を受け取る
    # どのルームへの投稿かは、HTMLのhidden項目
    # フォームの値は必ず文字で届くので、type=intで数値にして受け取る
    room_id = request.form.get("room_id", type=int)

    # 登録中のルーム以外への投稿は受け付けない。
    # 画面側でフォームを隠しているが、直接POSTを送られたときに防げないため、ここでも確認
    if room_id != get_joined_room_id(user_id):
        return redirect(url_for("post.posts_view", room_id=room_id))

    # .strip()で前後の余分な空白や改行を取り除く
    content = request.form.get("content", "").strip()

    # 添付画像（無ければNone）
    image_path = save_image(request.files.get("image"))

    # 空・スペースだけの投稿はDBに保存しない
    graduated = False
    if content != "" and room_id is not None:
        db_create_post(user_id, room_id, content, image_path)
        # 投稿したときだけ、連続日数の判定
        graduated = update_streak_and_check_graduation(user_id, room_id)

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
    user_id = CURRENT_USER_ID

    # どのルームか受け取る（戻り先の画面を決めるため）
    room_id = request.form.get("room_id", type=int)

    db_delete_post(post_id, user_id)

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
    user_id = CURRENT_USER_ID

    # どのルームか（戻り先）
    room_id = request.form.get("room_id", type=int)

    # 書きかえ後の本文を受け取る
    new_content = request.form.get("content", "").strip()

    # 新しい画像が送られてきたときだけ差しかえる（無ければNoneのまま＝既存画像を維持）
    image_path = save_image(request.files.get("image"))

    # 空の内容で保存されるのを防ぐ
    if new_content != "":
        db_update_post(post_id, user_id, new_content, image_path)

    # 投稿画面に戻る
    return redirect(url_for("post.posts_view", room_id=room_id))


@post_bp.route("/posts/<int:post_id>/reaction", methods=["POST"])
def react(post_id):
    """リアクションボタンが押されたとき（POST）の処理
    すでに押していれば取り消し、押していなければ登録
    自分の投稿には押せない、という確認はmodels側で行っている
    リアクションは、登録していないチャレンジルームでも可能。
    """
    user_id = CURRENT_USER_ID

    room_id = request.form.get("room_id", type=int)
    reaction_type = request.form.get("reaction_type", type=int)

    # 想定外の番号のときは、何もしない
    valid_types = [rt["type"] for rt in REACTION_TYPES]
    if reaction_type in valid_types:
        toggle_reaction(user_id, post_id, reaction_type)

    # 投稿画面に戻る
    return redirect(url_for("post.posts_view", room_id=room_id))


@post_bp.route("/posts/<int:post_id>/reply", methods=["POST"])
def reply_post(post_id):
    # 返信ボタンが押されたとき（POST）の処理
    user_id = CURRENT_USER_ID

    room_id = request.form.get("room_id", type=int)
    content = request.form.get("content", "").strip()

    if content != "" and room_id is not None:
        create_reply(user_id, room_id, post_id, content)

    return redirect(url_for("post.posts_view", room_id=room_id))
