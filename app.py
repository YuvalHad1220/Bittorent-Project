from flask import Flask, render_template, request, jsonify
from settings import read_settings_file
from app_operations import *
from torrent_handler import TorrentHandler
from utils import get_client_list

SUCCESS = {"success": True}
FAILURE = {"success": False}

torrent_handler = TorrentHandler("torrent.db")
settings = read_settings_file("settings.json")
app = Flask(__name__)
app.config["SECRET_KEY"] = "df0331cefc6c2b9a5d0208a726a5d1c0fd37324feba25506"

@app.route("/edit_settings", methods = ["GET", "POST"])
def edit_settings():
    if request.method == "GET":
        return jsonify(settings.asdict())

    update_settings(settings, request.get_json())
    
    return SUCCESS


@app.route('/get_available_clients', methods = ["GET"])
def get_available_clients():
    return get_client_list(False)


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
