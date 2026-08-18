# マイページ機能に関するDB操作を定義

from utils.db import get_connection


def get_mypage_user(user_id):
    """ユーザー情報を取得する"""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT name
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )

            user = cursor.fetchone()
            return user

    finally:
        connection.close()


def update_mypage_user(user_id, name):
    """ユーザー情報を更新する"""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET name = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (name, user_id,),
            )

            connection.commit()

    finally:
        connection.close()


def get_achievement_count(user_id):
    """達成カウントの取得"""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT achievement_count
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )

            achievement_data = cursor.fetchone()
            return achievement_data

    finally:
        connection.close()


def get_posted_days(user_id):
    """投稿した日数を取得する（午前3時が日付更新の境界）"""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                # 投稿日時を3時間戻して3時区切りの日付に変換し、投稿した日を重複なしで取得
                SELECT DISTINCT DATE(created_at - INTERVAL 3 HOUR) AS posted_date
                FROM posts
                WHERE user_id = %s
                    # 3時区切りで今日を含む過去30日間を取得
                    AND DATE(created_at - INTERVAL 3 HOUR) >= DATE(current_TIMESTAMP - INTERVAL 3 HOUR) - INTERVAL 29 DAY
                ORDER BY posted_date
                """,
                (user_id,),
            )

            posted_days = cursor.fetchall()
            return posted_days

    finally:
        connection.close()


def get_joined_room(user_id):
    """参加中のルーム情報を取得する"""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    rp.room_id,
                    r.name,
                    COUNT(mc.user_id) AS member_count
                FROM room_participations AS rp
                JOIN rooms AS r
                    ON rp.room_id = r.id
                # 同じルームの参加者を取得
                JOIN room_participations AS mc
                    ON rp.room_id = mc.room_id
                    AND mc.graduated_at IS NULL
                WHERE rp.user_id = %s
                    AND rp.graduated_at IS NULL
                # COUNT()で参加人数を集計するため、SELECTした項目をGROUP BY
                GROUP BY
                    rp.room_id,
                    r.name
                """,
                (user_id,),
            )

            joined_room = cursor.fetchone()
            return joined_room

    finally:
        connection.close()
