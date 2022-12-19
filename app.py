from flask import Flask, render_template

app = Flask(__name__)

@app.route('/', methods = ["GET"])
def homepage():
    title = "my torrent project"
    page = render_template("main-page.html", title = title)
    return page



if __name__ == "__main__":
    app.run(port=12345, debug=True)