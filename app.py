from flask import Flask, render_template, request, jsonify
from torrent import torrent
import random
app = Flask(__name__)

@app.route('/torrents', methods = ["POST"])
def ret_torrent_list():
    payload = request.json
    
    # first we will return an empty list so we can tell what to display
    return jsonify([torrent().asdict() for _ in range(random.randint(0,240))])


@app.route('/', methods = ["GET"])
def homepage():
    title = "my torrent project"
    page = render_template("main-page.html", title = title)
    return page



if __name__ == "__main__":
    app.run(port=12345, debug=True)