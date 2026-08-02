from flask import Blueprint, render_template

mypage_bp = Blueprint("mypage", __name__, url_prefix="/mypage")


@mypage_bp.route("/", methods=["GET"])
def index():
    return render_template("mypage.html")
