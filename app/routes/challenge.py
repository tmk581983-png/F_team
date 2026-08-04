from flask import Flask,render_template,Blueprint

challenge_bp = Blueprint("challenge",__name__, url_prefix="/challenge")

@challenge_bp.route("/room/<int:room_id>")
def room(room_id):
    if room_id == 1 :
      room_name="目指せ!150ステップ!"
      return render_template("challenge_room.html",room_name=room_name)

    elif room_id == 2 :
       room_name="いくぜ!ステップ200~!!"
       return render_template("challenge_room.html",room_name=room_name)

    elif room_id == 3 :
       room_name="ネットワークを極めたい!"
       return render_template("challenge_room.html",room_name=room_name)

    elif room_id == 4 :
       room_name="Linux王に俺はなる!"
       return render_template("challenge_room.html",room_name=room_name)

    elif room_id == 5 :
       room_name="言語化を制すものは!"
       return render_template("challenge_room.html",room_name=room_name)

    elif room_id == 6 :
       room_name="休ませてくれ・・"
       return render_template("challenge_room.html",room_name=room_name)
 
    else :
       return "Room not found", 404

@challenge_bp("/result")
def result():
   return render_template("result.html")

@challenge_bp("/room_select")
def room_select():
   return render_template("room_select.html")

if __name__ == "__main__":
    app.run(debug=True)



