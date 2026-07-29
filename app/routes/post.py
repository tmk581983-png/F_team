"""投稿画面（掲示板）の処理をまとめたファイル

【このファイルの役割】
ブラウザから「/posts を見せて」「投稿します」と言われたときに、
何をするかを決めている場所です。

【いまの状態】
データベースはまだ使わず、このファイルの中にある
ダミーデータ（下の ROOMS と POSTS）を表示しています。
あとで models/post.py（DB操作）に置きかえます。

【画面の流れ】
  ブラウザ  →  このファイル（routes/post.py）
                    ↓ データを渡す
              templates/post/posts.html
                    ↓ HTMLができる
  ブラウザに表示される
"""

# 日時を扱うための道具を読み込む（投稿日時に使います）
from datetime import datetime

# Flask（Webアプリを作る道具）から、必要な部品を読み込む
#   Blueprint      … 機能ごとにファイルを分けるための仕組み
#   render_template… HTMLファイルに値を差し込んで表示する
#   request        … ブラウザから送られてきた値を受け取る
#   redirect       … 別のページへ移動させる
#   url_for        … ページのアドレスを組み立てる
from flask import Blueprint, render_template, request, redirect, url_for


# ============================================================
# Blueprint（ブループリント）の作成
# ============================================================
# 「post」という名前で、投稿機能のルートをひとまとめにします。
# app.py で register_blueprint(post_bp) と書くことで有効になります。
#
# この名前は url_for で使います。（例：url_for("post.posts_view")）
post_bp = Blueprint("post", __name__)


# ============================================================
# ダミーデータ（あとでデータベースに置きかえる部分）
# ============================================================

# チャレンジルームの一覧
# ★ あとで rooms テーブルから取ってくる予定の部分です
#    ここを書きかえれば、プルダウンの中身が変わります
ROOMS = [
    {"id": "room_01", "name": "早起きチャレンジ"},
    {"id": "room_02", "name": "筋トレチャレンジ"},
    {"id": "room_03", "name": "読書チャレンジ"},
    {"id": "room_04", "name": "勉強チャレンジ"},
    {"id": "room_05", "name": "禁酒チャレンジ"},
]


# 投稿のダミーデータ
# ★ あとで posts テーブルから取ってくる予定の部分です
#
# 「ルームID」をカギにして、そのルームの投稿リストを持っています。
#   POSTS["room_01"] → room_01 の投稿が入ったリスト
#
# 1件の投稿が持っている情報：
#   id         … 投稿を見分けるための番号（削除するときに使う）
#   user_name  … 投稿した人の名前
#   content    … 投稿の本文
#   created_at … 投稿した日時
#   replies    … その投稿への返信（今回は表示だけ）
#   reactions  … リアクションの数（今回は表示だけ）
#   is_mine    … 自分の投稿なら True。自分の投稿だけ削除ボタンを出すため
#                ★ ログイン機能ができたら、
#                   「投稿した人のID == ログイン中の人のID」で判定します
POSTS = {
    "room_01": [
        {
            "id": 1,
            "user_name": "山田太郎",
            "content": "今日は5時に起きられました！朝日がきれいです。",
            "created_at": "2026-07-26 05:12",
            "replies": ["すごい！わたしも頑張ります", "早起き仲間ですね"],
            "reactions": 3,
            "is_mine": False,
        },
        {
            "id": 2,
            "user_name": "鈴木二郎",
            "content": "6時起き達成。3日連続です。",
            "created_at": "2026-07-26 06:03",
            "replies": ["連続記録おめでとうございます"],
            "reactions": 5,
            "is_mine": False,
        },
        {
            "id": 3,
            "user_name": "あなた",
            "content": "昨日は寝坊しましたが、今日は間に合いました。",
            "created_at": "2026-07-26 06:30",
            "replies": [],
            "reactions": 1,
            "is_mine": True,
        },
    ],
    "room_02": [
        {
            "id": 4,
            "user_name": "佐藤三郎",
            "content": "腕立て30回やりました。",
            "created_at": "2026-07-26 21:40",
            "replies": [],
            "reactions": 2,
            "is_mine": False,
        },
    ],
    "room_03": [
        {
            "id": 5,
            "user_name": "田中四郎",
            "content": "今日は20ページ読みました。",
            "created_at": "2026-07-26 22:15",
            "replies": ["どんな本ですか？"],
            "reactions": 1,
            "is_mine": False,
        },
    ],
    # 投稿がまだ無いルームは、空のリスト [] にしておきます
    "room_04": [],
    "room_05": [],
}


# ============================================================
# 補助の関数（画面の処理から呼び出す、小さな道具）
# ============================================================

def find_room_name(room_id):
    """ルームIDから、そのルームの名前を探して返す

    例： "room_01" を渡すと "早起きチャレンジ" が返ってきます。
    見つからなかったときは、空の文字 "" を返します。
    """
    # ROOMS のリストを、上から1つずつ見ていく
    for room in ROOMS:
        # IDが一致したら、その名前を返して終了
        if room["id"] == room_id:
            return room["name"]
    # 最後まで見つからなかった場合
    return ""


def make_new_post_id():
    """まだ使われていない、新しい投稿IDを作る

    すべてのルームの投稿を見て、いちばん大きいIDを探し、
    それに 1 を足したものを新しいIDとして返します。

    ★ データベースを使うようになれば、
       MySQL が AUTO_INCREMENT で自動採番してくれるので、
       この関数は不要になります。
    """
    all_ids = []

    # POSTS.values() は「すべてのルームの投稿リスト」を順に取り出します
    for post_list in POSTS.values():
        for post in post_list:
            all_ids.append(post["id"])

    # 投稿が1件も無いときは、最初のIDを 1 にする
    if len(all_ids) == 0:
        return 1

    # max() はリストの中でいちばん大きい数を返します
    return max(all_ids) + 1


# ============================================================
# 画面の処理（ここからが本体）
# ============================================================

@post_bp.route("/posts", methods=["GET"])
def posts_view():
    """掲示板ページを表示する

    【いつ動く？】
    ブラウザで /posts を開いたとき（GET）

    【やること】
    1. どのルームを見たいのかを受け取る
    2. そのルームの投稿を取り出す
    3. HTMLに渡して画面を作る
    """

    # --- 1. どのルームを見たいのか受け取る ---
    # アドレスの「?room_id=room_01」の部分を読み取ります。
    # request.args は「アドレスに付いてきた値」を受け取る箱です。
    #
    # 第2引数の ROOMS[0]["id"] は「指定が無かったときの初期値」。
    # ここでは、いちばん上のルーム（room_01）を表示します。
    #
    # ★ 前の画面から /posts?room_id=room_03 のように呼ばれれば、
    #    そのルームが最初から選ばれた状態で開きます。
    room_id = request.args.get("room_id", ROOMS[0]["id"])

    # --- 2. そのルームの投稿を取り出す ---
    # .get() は「カギが無ければ、代わりにこれを返して」という書き方。
    # 存在しないルームIDが来ても、エラーにならず空のリストになります。
    posts = POSTS.get(room_id, [])

    # --- 3. HTMLに値を渡して、画面を作る ---
    # ここで渡した名前（rooms、room_id など）が、
    # posts.html の中で {{ rooms }} のように使えるようになります。
    return render_template(
        "post/posts.html",
        rooms=ROOMS,                        # プルダウンに並べるルーム一覧
        room_id=room_id,                    # いま選ばれているルームID
        room_name=find_room_name(room_id),  # いま選ばれているルームの名前
        posts=posts,                        # 掲示板に並べる投稿
    )


@post_bp.route("/posts", methods=["POST"])
def create_post():
    """投稿ボタンが押されたときの処理

    【いつ動く？】
    投稿フォームの「投稿」ボタンが押されたとき（POST）

    【やること】
    1. フォームに入力された内容を受け取る
    2. 新しい投稿を作って、リストの先頭に追加する
    3. 掲示板ページに戻る

    ★ いまはデータベースではなく、上の POSTS に追加しています。
       そのため、コンテナを再起動すると投稿は消えます。
    """

    # --- 1. フォームの内容を受け取る ---
    # request.form は「フォームから送られてきた値」を受け取る箱です。
    # （アドレスに付いてくる値は request.args、フォームは request.form）

    # どのルームへの投稿かは、HTMLの hidden 項目で一緒に送られてきます
    room_id = request.form.get("room_id", ROOMS[0]["id"])

    # .strip() は、前後の余分な空白や改行を取り除きます
    content = request.form.get("content", "").strip()

    # --- 2. 新しい投稿を作って追加する ---
    # 空っぽの投稿は追加しない（スペースだけの投稿も防げます）
    if content != "":
        new_post = {
            "id": make_new_post_id(),
            "user_name": "あなた",
            "content": content,
            # strftime は日時を「2026-07-29 10:36」の形の文字にします
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "replies": [],
            "reactions": 0,
            # 自分が投稿したものなので True（削除ボタンが表示されます）
            "is_mine": True,
        }

        # setdefault は「そのルームのリストが無ければ、空のリストを作る」
        # insert(0, ...) は「リストの先頭に入れる」＝新しい投稿が一番上に出る
        POSTS.setdefault(room_id, []).insert(0, new_post)

    # --- 3. 掲示板ページに戻る ---
    # redirect は「別のページへ移動させる」命令です。
    # 投稿したあと、同じルームの掲示板をもう一度表示します。
    #
    # ★ 投稿後にわざわざ移動させるのは、
    #    ブラウザの更新ボタンで二重投稿になるのを防ぐためです。
    return redirect(url_for("post.posts_view", room_id=room_id))


@post_bp.route("/posts/<int:post_id>/delete", methods=["POST"])
def delete_post(post_id):
    """削除ボタンが押されたときの処理

    【いつ動く？】
    投稿の「削除」ボタンが押されたとき（POST）

    【アドレスの <int:post_id> について】
    /posts/3/delete のようにアクセスされると、
    真ん中の 3 が post_id という名前でこの関数に渡ってきます。
    int: と書いてあるので、数字だけを受け付けます。

    【やること】
    1. どのルームの、どの投稿を消すのかを特定する
    2. 自分の投稿かどうかを確認してから消す
    3. 掲示板ページに戻る
    """

    # --- 1. どのルームかを受け取る ---
    room_id = request.form.get("room_id", ROOMS[0]["id"])

    # そのルームの投稿リストを取り出す
    posts = POSTS.get(room_id, [])

    # --- 2. 目的の投稿を探して消す ---
    # リストを1件ずつ見ていき、IDが一致したものを削除します
    for post in posts:
        if post["id"] == post_id:

            # ★ 大事な確認 ★
            # 自分の投稿でなければ、削除せずに何もしません。
            # 画面上は他人の投稿に削除ボタンを出していませんが、
            # アドレスを直接打たれても消されないよう、ここでも確認します。
            if post["is_mine"]:
                posts.remove(post)

            # 見つかったので、これ以上さがす必要はありません
            # （リストを回している途中で消すため、必ず break で抜けます）
            break

    # --- 3. 掲示板ページに戻る ---
    return redirect(url_for("post.posts_view", room_id=room_id))
