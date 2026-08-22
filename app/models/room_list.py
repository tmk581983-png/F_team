# チャレンジルーム一覧機能に関するDB操作を定義

from utils.db import get_connection


def get_room_lists():
    """チャレンジルーム一覧を取得する"""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    r.id,
                    r.name,
                    COUNT(rp.user_id) AS member_count
                FROM rooms AS r
                LEFT JOIN room_participations AS rp
                    ON r.id = rp.room_id
                    AND rp.graduated_at IS NULL
                GROUP BY
                    r.id,
                    r.name
                """,
            )

            rooms = cursor.fetchall()
            return rooms

    finally:
        connection.close()


def create_room_participation(user_id, room_id):
    """room_participationsテーブルにルーム参加情報を登録する"""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO room_participations(user_id, room_id)
                VALUES(%s, %s)
                """,
                (user_id, room_id,),
            )

            connection.commit()

    finally:
        connection.close()
