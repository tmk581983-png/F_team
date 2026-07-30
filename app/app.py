from flask import Flask
from routes.mypage import mypage_bp

app = Flask(__name__)

# Blueprint登録
app.register_blueprint(mypage_bp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
