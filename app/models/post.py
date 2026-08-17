from utils.db import get_connection


def get_all_rooms():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM rooms ORDER BY id")
            return cur.fetchall()
    finally:
             conn.close()
        
def get_reactions_by_room(user_id, room_id):
    """ルーム内の各投稿について、リアクションの件数と自分の押下状態を取得する

    【なぜ投稿ごとに数えないのか】
    投稿が20件あるとDBへの問い合わせが20回発生してしまう。
    GROUP BY を使えば、1回の問い合わせで全部の集計が返ってくる。

    【1つのSQLにまとめている理由】
    「種類ごとの件数」と「自分が押したか」は同じ行から求められるため、
    2回に分けて問い合わせる必要がない。DBへの接続回数を減らせる。

    【SUM(reactions.user_id = %s) について】
    MySQLでは条件式が真なら1、偽なら0になる。
    それを合計すると「自分が押した件数」になる。
    UNIQUE制約があるので、結果は必ず 0 か 1 になる。

    【%s の順番に注意】
    SELECT の中の %s（user_id）が先、WHERE の %s（room_id）が後。
    渡す値も、その順番に合わせる必要がある。

    【戻り値】
    [{"post_id": 5, "reaction_type": 1, "count": 3, "mine": 1}, ...]
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    reactions.post_id,
                    reactions.reaction_type,
                    COUNT(*) AS count,
                    SUM(reactions.user_id = %s) AS mine
                FROM reactions
                JOIN posts ON reactions.post_id = posts.id
                WHERE posts.room_id = %s AND posts.deleted_at IS NULL
                GROUP BY reactions.post_id, reactions.reaction_type
                """,
                (user_id, room_id),
            )
            return cur.fetchall()
    finally:
        conn.close()


def toggle_reaction(user_id, post_id, reaction_type):
    """リアクションを押す／取り消す

    【処理】
    1. 自分の投稿でないか確認する（自分の投稿には押せない仕様）
    2. すでに押していれば削除、押していなければ登録

    【自分の投稿かどうかを、ここでも確認する理由】
    画面側でもボタンを押せないようにしているが、それだけでは
    アドレスを直接叩かれたときに防げない。削除・編集と同じ考え方で、
    サーバー側でも確認する。

    【なぜ「あれば削除」なのか】
    reactions テーブルには UNIQUE(user_id, post_id, reaction_type) が
    付いており、同じ人が同じ反応を2回登録できない。
    そのまま2回目をINSERTするとエラーになるので、
    「押してあれば取り消す」動き（トグル）にしている。
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # --- 1. 投稿の持ち主を調べる ---
            cur.execute(
                "SELECT user_id FROM posts WHERE id = %s AND deleted_at IS NULL",
                (post_id,),
            )
            post = cur.fetchone()

            # 投稿が無い、または自分の投稿なら、何もせず終了
            if post is None or post["user_id"] == user_id:
                return

            # --- 2. すでに押しているか調べる ---
            cur.execute(
                """
                SELECT id FROM reactions
                WHERE user_id = %s AND post_id = %s AND reaction_type = %s
                """,
                (user_id, post_id, reaction_type),
            )
            existing = cur.fetchone()

            # --- 3. あれば取り消し、なければ登録 ---
            if existing:
                cur.execute("DELETE FROM reactions WHERE id = %s", (existing["id"],))
            else:
                cur.execute(
                    """
                    INSERT INTO reactions (user_id, post_id, reaction_type)
                    VALUES (%s, %s, %s)
                    """,
                    (user_id, post_id, reaction_type),
                )
        conn.commit()
    finally:
        conn.close()


def get_posts_by_room(room_id):
    """指定したルームの投稿を、新しい順に取得する

    【SQLの意味】
    room_id が一致し、かつ deleted_at が NULL（＝削除されていない）投稿を、
    created_at（投稿日時）の新しい順に取り出す。

    posts テーブルには投稿者の「名前」が無く、user_id（番号）しか無いので、
    JOIN で users テーブルと結び付けて、name も一緒に取得する。
    　posts.user_id = users.id が一致する行どうしをつなげる、という意味。

    【%s について】
    SQL文の中に room_id をそのまま書き込むと、
    悪意のある文字列を入力されたときに危険（SQLインジェクション）。
    %s と書いておき、実際の値は別に渡すことで、安全に埋め込まれる。
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    posts.id,
                    posts.user_id,
                    posts.room_id,
                    posts.contents,
                    posts.created_at,
                    users.name AS user_name
                FROM posts
                JOIN users ON posts.user_id = users.id
                WHERE posts.room_id = %s AND posts.deleted_at IS NULL
                ORDER BY posts.created_at DESC
                """,
                (room_id,),
            )
            # fetchall() … 該当する行を全部、リストにして返す
            return cur.fetchall()
    finally:
        # 成功しても失敗しても、最後に必ず接続を閉じる
        conn.close()


def create_post(user_id, room_id, content):
    """投稿を1件、posts テーブルに保存する"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO posts (user_id, room_id, contents)
                VALUES (%s, %s, %s)
                """,
                (user_id, room_id, content),
            )
        # INSERT や UPDATE は、commit() しないと実際には保存されない
        conn.commit()
    finally:
        conn.close()


def delete_post(post_id, user_id):
    """自分の投稿だけを削除する（論理削除）

    【論理削除について】
    実際に行を消す（DELETE）のではなく、
    deleted_at に「消した日時」を記録するだけにしている。
    こうすると、間違えて消してもデータ自体は残っているので復元しやすい。

    【user_id も条件に入れている理由】
    「そのIDの投稿」かつ「自分が投稿したもの」の両方が一致したときだけ更新する。
    こうすることで、他人の投稿は消せないようにサーバー側でも守っている。
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE posts
                SET deleted_at = NOW()
                WHERE id = %s AND user_id = %s
                """,
                (post_id, user_id),
            )
        conn.commit()
    finally:
        conn.close()


def update_post(post_id, user_id, content):
    """自分の投稿だけを編集する"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE posts
                SET contents = %s
                WHERE id = %s AND user_id = %s
                """,
                (content, post_id, user_id),
            )
        conn.commit()
    finally:
        conn.close()
