from flask import Flask
from routes.login import login_bp
from routes.signup import signup_bp

app = Flask(__name__)

app.register_blueprint(login_bp)
app.register_blueprint(signup_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

