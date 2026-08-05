"""
投稿画面の処理

【R8.7.23現在】
DB接続はまだしないので、ダミーデータ（ ROOMS と POSTS）を表示。
後ほどmodels/post.py（DB操作）に置きかえ予定。

【処理の流れ】
ブラウザ → 本ファイル →（データを渡す）→ templates/posts.html → ブラウザに表示

"""

# 投稿日時
from datetime import datetime

#   Blueprint      … アプリを分割して管理する仕組み
#   render_template… flaskモジュールのFlaskクラスとrender_template関数。HTMLファイルに値を差し込んで表示
#   request        … ブラウザから送られてきた値（リクエスト）
#   redirect       … 別のページへ移動
#   url_for        … エンドポイントのURLを利用
from flask import Blueprint, render_template, request, redirect, url_for


# ============================================================
# Blueprintをインポート
# ============================================================
# 「post」という名前で、投稿機能のルートをひとまとめにする。
# app.py に register_blueprint(post_bp) を追記すると有効になる。らしい
# この名前は url_for 使用（例：url_for("post.posts_view")）
post_bp = Blueprint("post", __name__)

# チャレンジルームの一覧（プルダウンの中身）
# DB接続後に該当テーブルからパラメータを取得する
ROOMS = [
    {"id": "room_01", "name": "目指せ！150ステップクリア！"},
    {"id": "room_02", "name": "ネットワークわけわからん"},
    {"id": "room_03", "name": "今から日報書きます"},
    {"id": "room_04", "name": "言語化してみる"},
    {"id": "room_05", "name": "一休み一休み"},
]


# 投稿のダミーデータ
# DB接続後にposts テーブル？から取ってくる予定の処理
# 「ルームID」をキーにして、そのルームの投稿リストを持っている
#   POSTS["room_01"] → room_01 の投稿が入ったリスト
#
# 1件の投稿が持っている情報：
#   id         … 投稿を見分けるための番号（削除するときに使う）
#   user_name  … 投稿したユーザ
#   content    … 投稿文
#   created_at … 投稿した日時
#   replies    … 投稿への返信（今は表示のみ）
#   reactions  … リアクションの数（今は表示のみ）
#   is_mine    … 自分の投稿 = True　※自分の投稿のみ削除ボタンを表示
#               　投稿したユーザID = ログイン中のユーザID　で判定
POSTS = {
    "room_01": [
        {
            "id": 1,
            "user_name": "テスト1",
            "content": "今日は5ステップ進めました！",
            "created_at": "2026-07-26 05:12",
            "replies": ["すごい！わたしも頑張ります", "一緒にハッカソンに出場しましょう"],
            "reactions": 3,
            "is_mine": False,
        },
        {
            "id": 2,
            "user_name": "テスト2",
            "content": "150ステップ達成しました！",
            "created_at": "2026-07-26 06:03",
            "replies": ["おめでとうございます"],
            "reactions": 5,
            "is_mine": False,
        },
        {
            "id": 3,
            "user_name": "あなた",
            "content": "今日のステップは時間がかかるので、明日に完了させます",
            "created_at": "2026-07-26 06:30",
            "replies": [],
            "reactions": 1,
            "is_mine": True,
        },
    ],
    "room_02": [
        {
            "id": 4,
            "user_name": "テスト3",
            "content": "OSI参照モデルを覚えました",
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
            "content": "日報提出でしました！あと1分のところでギリギリセーフ！",
            "created_at": "2026-07-26 22:15",
            "replies": ["よかったですね！私は間に合いませんでした。涙"],
            "reactions": 1,
            "is_mine": False,
        },
    ],
    # 投稿がまだ無いルームは、空のリスト [] 
    "room_04": [],
    "room_05": [],
}


# ============================================================
# 補助の関数（画面の処理から呼び出す）
# ============================================================

def find_room_name(room_id):
    """ルームIDから、ルーム名を探して返す
    見つからなかったときは、空の文字 "" を返す
    """
    # ROOMS のリストを、上から1つずつ見ていく
    for room in ROOMS:
        # IDが一致したら、ルーム名を返して終了
        if room["id"] == room_id:
            return room["name"]
    # 最後まで見つからなかった場合
    return ""


def make_new_post_id():
    """新しい投稿ID作成
    すべての投稿から最大値のIDを探し、+1 して新しいIDを返す
    データベースを使うようになると、MySQL が AUTO_INCREMENT で自動採番してくれるため、この関数は不要になる
    """
    all_ids = []

    # POSTS.values() は「ルームのすべての投稿」を順に取り出す
    for post_list in POSTS.values():
        for post in post_list:
            all_ids.append(post["id"])

    # 投稿が1件も無いときは、最初のIDを 1 にする
    if len(all_ids) == 0:
        return 1

    # リストの中でいちばん大きい数を返す
    return max(all_ids) + 1

# ============================================================
# 画面の処理（本体）
# ============================================================
@post_bp.route("/posts", methods=["GET"])
def posts_view():
    #ブラウザで /posts を開いたとき（GET）に投稿ページを表示する。

    # --- 1. どのルームを見たいのか受け取る ---
    # アドレスの「?room_id=room_01」の部分を読み取り
    # request.args は「アドレスに付いてきた値」を受け取る
    # 第2引数の ROOMS[0]["id"] は「指定が無かったときの初期値」。
    # ここでは、いちばん上のルーム（room_01）を表示。
    #前の画面から /posts?room_id=room_03 のように呼ばれると、
    #そのルームが最初から選ばれた状態で開く。
    room_id = request.args.get("room_id", ROOMS[0]["id"])

    # --- 2. そのルームの投稿を取り出す ---
    # .get() は「キーが無ければ、代わりにこれを返して」という処理
    # 存在しないルームIDが来ても、エラーにならず空のリストになる。
    posts = POSTS.get(room_id, [])

    # --- 3. HTMLに値を渡して、画面作成 ---
    # ここで渡した項目（rooms、room_id など）が、
    # posts.html の中で {{ rooms }} のように使えるようになる。
    return render_template(
        "posts.html",
        rooms=ROOMS,                        # プルダウンのルーム一覧
        room_id=room_id,                    # 選択されているルームID
        room_name=find_room_name(room_id),  # 選択されているルーム名
        posts=posts,                        # 投稿画面に表示する投稿
    )


@post_bp.route("/posts", methods=["POST"])
def create_post():
    """投稿ボタンを押したときの処理

    【処理】
    1. 投稿フォームに入力された内容を受け取る
    2. 新しい投稿を作って、リストの先頭に追加する
    3. 投稿画面に戻る

    ★ データベースに接続するまでは、上の POSTS に追加。
       このため、コンテナを再起動すると投稿は消える。
    """

    # request.form は「フォームから送られてきた値」を受け取る。
    # （アドレスに付いてくる値は request.args、フォームは request.form）

    # どのルームへの投稿かは、HTMLの hidden 項目で一緒に送られてくる
    room_id = request.form.get("room_id", ROOMS[0]["id"])

    # .strip() は、前後の余分な空白や改行を取り除く
    content = request.form.get("content", "").strip()

    # 新しい投稿を作って追加する
    # 空っぽの投稿は追加しない（スペースだけの投稿も防ぐ）
    if content != "":
        new_post = {
            "id": make_new_post_id(),
            "user_name": "あなた",
            "content": content,
            # strftime は日時を「YYYY-MM-DD HH:MM」の形にする
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "replies": [],
            "reactions": 0,
            # 自分が投稿したものなので True（削除ボタン表示）
            "is_mine": True,
        }

        # setdefault は「そのルームのリストが無ければ、空のリストを作る」
        # insert(0, ...) は「リストの先頭に入れる」＝新しい投稿が一番上に出る
        POSTS.setdefault(room_id, []).insert(0, new_post)

    # 投稿画面に戻る
    # redirect は「別のページへ移動させる」処理。
    # 投稿したあと、同じルームの投稿画面をもう一度表示する。
    # 投稿後に移動させるのは、ブラウザの更新ボタンで二重投稿になるのを防ぐため。
    return redirect(url_for("post.posts_view", room_id=room_id))


@post_bp.route("/posts/<int:post_id>/delete", methods=["POST"])
def delete_post(post_id):
    """削除ボタンが押されたとき（POST）の処理
    【アドレスの <int:post_id> について】
    /posts/3/delete のようにアクセスされると、真ん中の 3 が post_id という名前でこの関数に渡される。
    int:なので数字だけ受け付け。

    【処理内容】
    1. どのルームの、どの投稿を削除するのか特定
    2. 自分の投稿かどうかを確認してから削除
    3. 投稿画面に戻る
    """

    # どのルームかを受け取る
    room_id = request.form.get("room_id", ROOMS[0]["id"])

    # そのルームの投稿リストを取り出す
    posts = POSTS.get(room_id, [])

    # 目的の投稿を探して削除（リストを1件ずつ見ていき、IDが一致したものを削除する）
    for post in posts:
        if post["id"] == post_id:
            # 自分の投稿でなければ、削除せずに何もしない
            # 画面上は他人の投稿に削除ボタンを出していないが、
            # アドレスを直接打たれても消されないよう、ここでも確認する。
            if post["is_mine"]:
                posts.remove(post)
            # 見つかったので、これ以上さがす必要はない
            # （リストを回している途中で消すため、必ず break で抜ける）
            break

    # 投稿画面に戻る
    return redirect(url_for("post.posts_view", room_id=room_id))
