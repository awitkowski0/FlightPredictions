import os
import datetime

from flask import Flask, render_template, request
app = Flask(__name__)


@app.route("/")
@app.route("/index")
def index():
	return render_template("index.html")


if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')
