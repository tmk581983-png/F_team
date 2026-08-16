from flask import Flask,render_template,Blueprint
from utils.db import get_connection

challenge_bp = Blueprint("challenge",__name__, url_prefix="/challenge")

@challenge_bp.route("/room/<int:room_id>")
def room(room_id):
    if room_id == 1 :
      room_name="目指せ!150ステップ!"

    elif room_id == 2 :
       room_name="いくぜ!ステップ200~!!"

    elif room_id == 3 :
       room_name="ネットワークを極めたい!"

    elif room_id == 4 :
       room_name="Linux王に俺はなる!"

    elif room_id == 5 :
       room_name="言語化を制すものは!"


    elif room_id == 6 :
       room_name="休ませてくれ・・"
       
    else :
       return "Room not found", 404

    conn = get_connection()
    cursor = conn.cursor()

   # 現在の参加者を探す→各参加者の最新日時を探す→その日時の投稿を特定
    sql = """
    SELECT
    u.name,
    p.contents
    FROM room_participations AS rp

    JOIN users AS u
      ON rp.user_id = u.id

    LEFT JOIN (
      SELECT
         user_id,
         room_id,
         MAX(created_at) AS latest_created_at
      FROM posts
      GROUP BY user_id, room_id
    ) AS lp
      ON rp.user_id = lp.user_id
      AND rp.room_id = lp.room_id

    LEFT JOIN posts AS p
      ON rp.user_id = p.user_id
      AND rp.room_id = p.room_id
      AND p.created_at = lp.latest_created_at

    WHERE rp.room_id = %s
    AND rp.graduated_at IS NULL;
    """
    
    cursor.execute(sql, (room_id,))
    users = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("challenge_room.html",room_name=room_name, users=users)
     

@challenge_bp.route("/result")
def result():
   return render_template("result.html")

@challenge_bp.route("/room_select")
def room_select():
   return render_template("room_select.html")





