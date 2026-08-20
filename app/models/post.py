from utils.db import get_connection


def get_all_rooms():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM rooms ORDER BY id")
            return cur.fetchall()
    finally:
        conn.close()


def get_joined_room_id(user_id):
    """ユーザーの登録IDを返すが、どこにも登録していなければ None
    graduated_at IS NULL
    卒業した日時が入っていない ＝ チャレンジルーム登録中
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT room_id
                FROM room_participations
                WHERE user_id = %s AND graduated_at IS NULL
                LIMIT 1
                """,
                (user_id,),
            )
            row = cur.fetchone()
            return row["room_id"] if row else None
    finally:
        conn.close()


def has_posted_today(user_id, room_id):
    # 指定したルームで、今日（3:00〜2:59）投稿済みか判定
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT last_posted_at
                FROM room_participations
                WHERE user_id = %s AND room_id = %s AND graduated_at IS NULL
                LIMIT 1
                """,
                (user_id, room_id),
            )
            row = cur.fetchone()
            if row is None or row["last_posted_at"] is None:
                return False

            cur.execute(
                "SELECT DATE(NOW() - INTERVAL 3 HOUR) = DATE(%s - INTERVAL 3 HOUR) AS is_today",
                (row["last_posted_at"],),
            )
            return bool(cur.fetchone()["is_today"])
    finally:
        conn.close()


def update_streak_and_check_graduation(user_id, room_id):
    """投稿の連続日数を更新し、3日連続達成で卒業
    3:00〜翌2:59 を1日とする(時刻から3時間引いてから日付だけを見る)

    【処理の流れ】
    1. 登録中（graduated_at IS NULL）の room_participations を取得
    2. 前回日（last_posted_at）と比較
       ・同じ日なら何もしない（2回目以降の投稿なのでカウントしない）
       ・前回の翌日なら streak +1
       ・それ以外（空白あり）streakを1に戻す（今日が1日目）
    3. streakが3になったら、graduated_atに日時を保存して
       users.achievement_countを+1

    【戻り値】
    True：3日連続達成。卒業した
    False：卒業していない（streakを更新しただけか対象データなし）
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 録中の参加記録を取得 ---
            cur.execute(
                """
                SELECT id, last_posted_at, current_streak_days
                FROM room_participations
                WHERE user_id = %s AND room_id = %s AND graduated_at IS NULL
                LIMIT 1
                """,
                (user_id, room_id),
            )
            participation = cur.fetchone()

            # 登録記録が無ければ何もしない
            if participation is None:
                return False

            # 3:00〜2:59
            cur.execute("SELECT DATE(NOW() - INTERVAL 3 HOUR) AS today")
            today = cur.fetchone()["today"]

            last_posted_at = participation["last_posted_at"]
            streak = participation["current_streak_days"]

            if last_posted_at is not None:
                cur.execute(
                    "SELECT DATE(%s - INTERVAL 3 HOUR) AS last_day",
                    (last_posted_at,),
                )
                last_day = cur.fetchone()["last_day"]
            else:
                last_day = None

            # streak更新
            if last_day == today:
                # 2回目以降の投稿なら何もしない
                return False
            elif last_day is not None and (today - last_day).days == 1:
                # 前回の翌日なので連続
                streak += 1
            else:
                # 初回、または空白。今日を1日目としてリセット
                streak = 1

            # 3日連続達成なら卒業
            graduated = streak >= 3

            if graduated:
                cur.execute(
                    """
                    UPDATE room_participations
                    SET current_streak_days = %s,
                        last_posted_at = NOW(),
                        graduated_at = NOW()
                    WHERE id = %s
                    """,
                    (streak, participation["id"]),
                )
                cur.execute(
                    "UPDATE users SET achievement_count = achievement_count + 1 WHERE id = %s",
                    (user_id,),
                )
            else:
                cur.execute(
                    """
                    UPDATE room_participations
                    SET current_streak_days = %s,
                        last_posted_at = NOW()
                    WHERE id = %s
                    """,
                    (streak, participation["id"]),
                )

        conn.commit()
        return graduated
    finally:
        conn.close()


def get_posts_view_data(user_id, room_id):
    """投稿画面の表示に必要なデータを、1回の接続でまとめて取得
    ルーム一覧、投稿、リアクションを別々の関数で呼ぶと接続3回となり接続確立に時間がかかる
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # ルーム一覧
            cur.execute("SELECT id, name FROM rooms ORDER BY id")
            rooms = cur.fetchall()

            posts = []
            reactions = []
            replies = []
            if room_id is not None:
                # 投稿（返信を除く。parent_post_id IS NULL のものだけ）
                cur.execute(
                    """
                    SELECT
                        posts.id,
                        posts.user_id,
                        posts.room_id,
                        posts.content,
                        posts.created_at,
                        users.name AS user_name
                    FROM posts
                    JOIN users ON posts.user_id = users.id
                    WHERE posts.room_id = %s
                      AND posts.deleted_at IS NULL
                      AND posts.parent_post_id IS NULL
                    ORDER BY posts.created_at DESC
                    """,
                    (room_id,),
                )
                posts = cur.fetchall()

                # リアクション
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
                reactions = cur.fetchall()

                # 返信（parent_post_id の値がある） 
                # postsテーブルをAS repliesで扱うß
                cur.execute(
                    """
                    SELECT
                        replies.id,
                        replies.parent_post_id,
                        replies.content,
                        replies.created_at,
                        users.name AS user_name
                    FROM posts AS replies
                    JOIN users ON replies.user_id = users.id
                    WHERE replies.room_id = %s
                      AND replies.deleted_at IS NULL
                      AND replies.parent_post_id IS NOT NULL
                    ORDER BY replies.created_at ASC
                    """,
                    (room_id,),
                )
                replies = cur.fetchall()

        return rooms, posts, reactions, replies
    finally:
        conn.close()


def create_reply(user_id, room_id, parent_post_id, content):
    """返信をposts テーブルに保存する（parent_post_idの値がある投稿）
    自分の投稿であれば、返信できない
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id FROM posts WHERE id = %s AND deleted_at IS NULL",
                (parent_post_id,),
            )
            parent = cur.fetchone()

            if parent is None or parent["user_id"] == user_id:
                return

            cur.execute(
                """
                INSERT INTO posts (user_id, room_id, content, parent_post_id)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, room_id, content, parent_post_id),
            )
        conn.commit()
    finally:
        conn.close()


def get_reactions_by_room(user_id, room_id):
    """投稿が件数分DBへの問い合わせも発生する
    GROUP BYなら1回の問い合わせで集計できる

    SUM(reactions.user_id = %s) について
    MySQLで条件式が真=1、偽=0になり
    それを合計すると「自分が押した件数」になる
    UNIQUE制約があるので、結果は必ず0か1
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
    自分の投稿でないか確認（自分の投稿は押せない）
    画面側でもボタンを押せないようにしているが、それだけでは
    アドレスを直接叩かれたときに防げないのでサーバー側でも確認
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 投稿主を確認
            cur.execute(
                "SELECT user_id FROM posts WHERE id = %s AND deleted_at IS NULL",
                (post_id,),
            )
            post = cur.fetchone()

            # 投稿がない、または自分の投稿なら終了
            if post is None or post["user_id"] == user_id:
                return

            # すでに押しているか調べる
            cur.execute(
                """
                SELECT id FROM reactions
                WHERE user_id = %s AND post_id = %s AND reaction_type = %s
                """,
                (user_id, post_id, reaction_type),
            )
            existing = cur.fetchone()

            # あれば取り消し、なければ登録
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
    room_id が一致し、かつdeleted_at がNULL（＝削除されていない）を
    created_at（投稿日時）の新しい順に取り出す。
    posts テーブルには投稿者の「名前」がなく、user_idしかないので、
    JOINでusers テーブルを結合してnameも取得

    %s → SQLの中に room_id をそのまま書き込むとSQLインジェクションに遭うリスクあり
    %sと書いておき、実際の値は別に渡す
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
                    posts.content,
                    posts.created_at,
                    users.name AS user_name
                FROM posts
                JOIN users ON posts.user_id = users.id
                WHERE posts.room_id = %s AND posts.deleted_at IS NULL
                ORDER BY posts.created_at DESC
                """,
                (room_id,),
            )
            #　該当行を返す
            return cur.fetchall()
    finally:
        # 接続を閉じる
        conn.close()


def create_post(user_id, room_id, content):
    # 投稿をpostsテーブルに保存
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO posts (user_id, room_id, content)
                VALUES (%s, %s, %s)
                """,
                (user_id, room_id, content),
            )
        #INSERTやUPDATEは、commit()しないと保存されない
        conn.commit()
    finally:
        conn.close()


def delete_post(post_id, user_id):
    """自分の投稿だけ削除（論理削除）

    【論理削除】
    実際に行を消す（DELETE）のではなく、deleted_at に「消した日時」を記録するだけ
    この場合、間違えて消してもデータ自体は残っているので復元可能

    【user_id も条件に入れている理由】
    「そのIDの投稿」かつ「自分が投稿したもの」の両方が一致したときだけ更新
    　他人の投稿は消せないようにサーバー側でも判定
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
    # 自分の投稿だけを編集
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE posts
                SET content = %s
                WHERE id = %s AND user_id = %s
                """,
                (content, post_id, user_id),
            )
        conn.commit()
    finally:
        conn.close()
