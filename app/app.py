from flask import Flask, render_template, request
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        user_id = request.form["user_id"]
        print(user_id)
        
    return render_template('login.html')

if __name__ == "__main__":
    app.run(debug=True)