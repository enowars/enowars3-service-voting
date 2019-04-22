from flask import Flask

app = Flask(__name__)

@app.route("/python")
def hello():
    return "<h3>Whupp whupp</h3>"

