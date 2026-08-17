"""
投稿画面の処理

【R8.8.16 更新】
posts テーブルへのDB接続
一覧の取得・投稿・削除・編集は、すべて models/post.py 経由

チャレンジルームの一覧も rooms テーブルから取得するようにした。
ファイル内に直接書いていたリスト（ROOMS）は削除している。

【まだダミーのままの部分】
・reactions（応援！／すごい！／共感！） … reactions テーブルとの連携が必要
・is_mine（自分の投稿かどうか） … ログイン機能が session にユーザーIDを
  保存するようになったら、session["user_id"] と比較する形に直す。
  それまでは CURRENT_USER_ID（下で定義）を「いまログインしている人」として仮に使う。

【処理の流れ】
ブラウザ → 本ファイル →（models/post.py 経由でDBを読み書き）→ templates/posts.html → ブラウザに表示
"""

#   Blueprint      … アプリを分割して管理する仕組み
#   render_template… flaskモジュールのFlaskクラスとrender_template関数。HTMLファイルに値を差し込んで表示
#   request        … ブラウザから送られてきた値（リクエスト）
#   redirect       … 別のページへ移動
#   url_for        … エンドポイントのURLを利用
from flask import Blueprint, render_template, request, redirect, url_for

from models.post import (
    get_all_rooms,
    get_posts_by_room,
    get_reactions_by_room,
    toggle_reaction,
    create_post as db_create_post,
    delete_post as db_delete_post,
    update_post as db_update_post,
)


# ============================================================
# Blueprintをインポート
# ============================================================
# 「post」という名前で、投稿機能のルートをひとまとめにする。
# app.py に register_blueprint(post_bp) を追記すると有効になる。らしい
# この名前は url_for 使用（例：url_for("post.posts_view")）
post_bp = Blueprint("post", __name__)

# チャレンジルームの一覧は、models/post.py の get_all_rooms() 経由で
# rooms テーブルから取得する。ここに直接書かない。

# ★ ログイン機能が未実装のため、仮の「いまログインしている人」のID。
#    session["user_id"] が使えるようになったら、この行ごと削除して
#    各関数の中で session.get("user_id") を使う形に置きかえる。
CURRENT_USER_ID = 1

# リアクションの種類
# DBの reactions.reaction_type に入る番号と、画面表示の対応表。
# 種類は仕様上3つで固定のため、マスタテーブルは作らずここで持つ。
#
# ★ 画像を用意したら、"emoji" を "image" に置きかえて
#    posts.html 側を <img> にすれば差し替えられる。
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

    rooms は get_all_rooms() で取ってきた一覧。
    DBを2回引かずに済むよう、取得済みの一覧を渡してもらう形にしている。
    """
    # rooms のリストを、上から1つずつ見ていく
    for room in rooms:
        # IDが一致したら、ルーム名を返して終了
        if room["id"] == room_id:
            return room["name"]
    # 最後まで見つからなかった場合
    return ""


def to_view_posts(rows, reactions):
    """DBから取ってきた行を、posts.html が扱いやすい形に整える

    【引数】
    rows      … get_posts_by_room() の結果（投稿そのもの）
    reactions … get_reactions_by_room() の結果（件数＋自分の押下状態）

    【やっていること】
    1. created_at（datetime型）を「2026-08-16 09:30」の文字に直す
    2. is_mine（自分の投稿かどうか）を追加する
    3. リアクションを、種類ごとの件数と押下状態に組み立てる
    """
    # --- リアクションを、引きやすい形に変換する ---
    # {投稿ID: {種類番号: {"count": 件数, "mine": 押したか}}}
    reaction_map = {}
    for row in reactions:
        reaction_map.setdefault(row["post_id"], {})[row["reaction_type"]] = {
            "count": row["count"],
            # SUM の結果は Decimal 型で返るため、int に直してから判定する
            "mine": int(row["mine"] or 0) > 0,
        }

    posts = []
    for row in rows:
        post_id = row["id"]

        # この投稿のリアクションを、種類ごとに組み立てる
        reactions_view = []
        for rt in REACTION_TYPES:
            # この投稿・この種類のデータ（誰も押していなければ None）
            data = reaction_map.get(post_id, {}).get(rt["type"])
            reactions_view.append({
                "type": rt["type"],
                "label": rt["label"],
                "emoji": rt["emoji"],
                "count": data["count"] if data else 0,
                # 自分が押しているか（ボタンの色を変えるために使う）
                "active": data["mine"] if data else False,
            })

        posts.append({
            "id": post_id,
            "user_name": row["user_name"],
            "content": row["contents"],
            "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M"),
            "is_mine": row["user_id"] == CURRENT_USER_ID,
            "reactions": reactions_view,
            # ★ 返信機能は未実装（いまは常に空）
            "replies": [],
        })
    return posts


# ============================================================
# 画面の処理（本体）
# ============================================================
@post_bp.route("/posts", methods=["GET"])
def posts_view():
    #ブラウザで /posts を開いたとき（GET）に投稿ページを表示する。

    # --- 1. ルームの一覧をDBから取り出す ---
    # プルダウンの中身になる。rooms テーブルが空なら空のリストが返る。
    rooms = get_all_rooms()

    # --- 2. どのルームを見たいのか受け取る ---
    # アドレスの「?room_id=1」の部分を読み取り
    # request.args は「アドレスに付いてきた値」を受け取る
    # type=int を付けると、文字の "1" ではなく数値の 1 で受け取れる。
    # （DBの rooms.id が数値なので、そろえておくと比較で迷わない）
    #前の画面から /posts?room_id=3 のように呼ばれると、
    #そのルームが最初から選ばれた状態で開く。
    room_id = request.args.get("room_id", type=int)

    # 指定が無かったときは、いちばん上のルームを表示する。
    # ルームが1件も無いときは None のままにして、下でDBを引かないようにする。
    if room_id is None:
        room_id = rooms[0]["id"] if rooms else None

    # --- 3. そのルームの投稿とリアクションをDBから取り出す ---
    if room_id is not None:
        posts = to_view_posts(
            get_posts_by_room(room_id),                       # 投稿そのもの
            get_reactions_by_room(CURRENT_USER_ID, room_id),  # リアクション
        )
    else:
        posts = []

    # --- 4. 投稿ボタンを押したか判定 ---
    # 「posted=1」で、マイページへ戻るボタンを押せる
    posted = request.args.get("posted") == "1"

    # --- 5. 「いま編集中の投稿」があるか ---
    edit_id = request.args.get("edit_id", type=int)

    # --- 6. HTMLに値を渡して、画面作成 ---
    return render_template(
        "posts.html",
        rooms=rooms,                               # プルダウンのルーム一覧
        room_id=room_id,                           # 選択されているルームID
        room_name=find_room_name(rooms, room_id),  # 選択されているルーム名
        posts=posts,                        # 投稿画面に表示する投稿
        posted=posted,                      # 投稿ボタンを押した後
        edit_id=edit_id,                    # いま編集中の投稿ID
    )


@post_bp.route("/posts", methods=["POST"])
def create_post():
    """投稿ボタンを押したときの処理

    【処理】
    1. 投稿フォームに入力された内容を受け取る
    2. DBの posts テーブルに保存する
    3. 投稿画面に戻る
    """

    # request.form は「フォームから送られてきた値」を受け取る。
    # （アドレスに付いてくる値は request.args、フォームは request.form）

    # どのルームへの投稿かは、HTMLの hidden 項目で一緒に送られてくる。
    # フォームの値は必ず文字で届くので、type=int で数値に直して受け取る。
    room_id = request.form.get("room_id", type=int)

    # .strip() は、前後の余分な空白や改行を取り除く
    content = request.form.get("content", "").strip()

    # 空・スペースだけの投稿はDBに保存しない
    if content != "" and room_id is not None:
        db_create_post(CURRENT_USER_ID, room_id, content)

    # 投稿画面に戻る
    return redirect(url_for("post.posts_view", room_id=room_id, posted=1))


@post_bp.route("/posts/<int:post_id>/delete", methods=["POST"])
def delete_post(post_id):
    """削除ボタンが押されたとき（POST）の処理
    【処理内容】
    1. どのルームの投稿を削除するのか特定
    2. DB側で「自分の投稿かどうか」を確認しつつ削除（models/post.py 内）
    3. 投稿画面に戻る

    ※ 自分の投稿でなければ、models 側の WHERE 条件に一致しないため、
       何も削除されずに終わる。アドレスを直接打たれても安全。
    """

    # どのルームか受け取る（戻り先の画面を決めるために使う）
    room_id = request.form.get("room_id", type=int)

    db_delete_post(post_id, CURRENT_USER_ID)

    # 投稿画面に戻る
    return redirect(url_for("post.posts_view", room_id=room_id))

@post_bp.route("/posts/<int:post_id>/edit", methods=["POST"])
def edit_post(post_id):
    """「保存する」ボタンが押されたとき（POST）の処理
    【処理内容】
    1. どのルームの投稿を編集するのか特定
    2. DB側で「自分の投稿かどうか」を確認しつつ書きかえる（models/post.py 内）
    3. 投稿画面に戻る（編集フォームは閉じる）
    """

    # どのルームかを受け取る（戻り先の画面を決めるために使う）
    room_id = request.form.get("room_id", type=int)

    # 書きかえた後の本文を受け取る
    new_content = request.form.get("content", "").strip()

    # 空の内容で保存されるのを防ぐ
    if new_content != "":
        db_update_post(post_id, CURRENT_USER_ID, new_content)

    # 投稿画面に戻る
    return redirect(url_for("post.posts_view", room_id=room_id))


@post_bp.route("/posts/<int:post_id>/reaction", methods=["POST"])
def react(post_id):
    """リアクションボタンが押されたとき（POST）の処理

    すでに押していれば取り消し、押していなければ登録する（トグル）。
    自分の投稿には押せない、という確認は models 側で行っている。

    ※ リアクションは、登録していないチャレンジルームでも可能。
       投稿は「自分の課題達成の記録」なので登録ルームに限るが、
       リアクションは「他の人を応援する行為」であり、
       応援できる範囲を狭める理由がないため。
    """
    room_id = request.form.get("room_id", type=int)
    reaction_type = request.form.get("reaction_type", type=int)

    # 想定外の番号が送られてきたときは、何もしない
    valid_types = [rt["type"] for rt in REACTION_TYPES]
    if reaction_type in valid_types:
        toggle_reaction(CURRENT_USER_ID, post_id, reaction_type)

    # 投稿画面に戻る
    return redirect(url_for("post.posts_view", room_id=room_id))
