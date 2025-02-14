# save this as app.py
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, World!"


if __name__ == '__main__':

    # run() method of Flask class runs the application 
    # on the local development server.
    app.run()