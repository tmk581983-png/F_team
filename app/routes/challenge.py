from flask import Flask,render_template,Blueprint,session, redirect, url_for
from utils.db import get_connection

challenge_bp = Blueprint("challenge",__name__, url_prefix="/challenge")

@challenge_bp.route("/room/<int:room_id>")
def room(room_id):

   user_id = session.get("user_id")
   if user_id is None:
      return redirect(url_for("login.login"))
   

   conn = get_connection()
   cursor = conn.cursor()

   try:
      room_sql = """SELECT name FROM rooms WHERE id = %s ;"""
      cursor.execute(room_sql, (room_id,))
      room = cursor.fetchone()

      if room is None:
         return "Room not found", 404

      room_name = room["name"]

      # 現在の参加者を探す→各参加者の最新日時を探す→その日時の投稿を特定
      sql = """
      SELECT
      u.name,
      p.content
      FROM room_participations AS rp

      JOIN users AS u
         ON rp.user_id = u.id

      LEFT JOIN (
         SELECT
            user_id,
            room_id,
            MAX(created_at) AS latest_created_at
         FROM posts
         WHERE deleted_at IS NULL
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
   finally:
      cursor.close()
      conn.close()

   return render_template("challenge_room.html",room_name=room_name, users=users)
   

@challenge_bp.route("/result")
def result():
   return render_template("result.html")

@challenge_bp.route("/room_select")
def room_select():
   return render_template("room_select.html")





