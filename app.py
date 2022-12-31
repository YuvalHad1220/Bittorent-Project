from flask import Flask, render_template, request, jsonify
from torrent import Torrent
from app_operations import handle_torrent
from torrent_handler import TorrentHandler

torrent_handler = TorrentHandler("torrent.db")
app = Flask(__name__)
app.config["SECRET_KEY"] = "df0331cefc6c2b9a5d0208a726a5d1c0fd37324feba25506"


@app.route("/torrents", methods=["POST"])
def ret_torrent_list():
    payload = request.json

    # first we will return an empty list so we can tell what to display
    return jsonify([torrent_obj.asdict() for torrent_obj in torrent_handler.get_torrents()])

@app.route("/create_torrentx", methods=["GET", "POST"])
def create_torrentx():
    if request.method == "POST":
        print("got post")

        
    return render_template("create-torrentx-page.html")


@app.route("/add_torrent", methods=["GET", "POST"])
def add_torrent():
    if request.method == "POST":
        handle_torrent(request, torrent_handler)


    return render_template("add-torrent-files-page.html")


@app.route("/", methods=["GET"])
def homepage():
    title = "my torrent project"
    page = render_template("main-page.html", title=title)
    return page

if __name__ == "__main__":
    app.run(port=12345, debug=False)
