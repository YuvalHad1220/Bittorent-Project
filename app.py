from flask import Flask, render_template, request, jsonify
from torrent import torrent
import random
app = Flask(__name__)
app.config['SECRET_KEY'] = "df0331cefc6c2b9a5d0208a726a5d1c0fd37324feba25506"
@app.route('/torrents', methods = ["POST"])
def ret_torrent_list():
    payload = request.json
    
    # first we will return an empty list so we can tell what to display
    return jsonify([torrent().asdict() for _ in range(random.randint(0,240))])


@app.route('/create_torrentx', methods=["GET", "POST"])
def create_torrentx():
    if request.method == "POST":

        print("got post")
    return render_template('create-torrentx-page.html')

@app.route('/add_torrent', methods = ["GET", "POST"])
def add_torrent():
    return render_template('add-torrent-files-page.html')


@app.route('/', methods = ["GET"])
def homepage():
    title = "my torrent project"
    page = render_template("main-page.html", title = title)
    return page



if __name__ == "__main__":
    app.run(port=12345, debug=True)