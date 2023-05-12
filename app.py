from flask import Flask, render_template, request, jsonify, redirect, url_for
from settings.settings import read_settings_file
from app_operations import *
from database.torrent_handler import TorrentHandler
from utils import get_client_list
from trakcer_announce_handler import main_loop
import threading
from thread_handler import ThreadHandler

SUCCESS = {"success": True}
FAILURE = {"success": False}

torrent_handler = TorrentHandler("./database/torrent.db")

# torrent = torrent_handler.get_torrents()[0]

# torrent.downloaded = 234234

# torrent_handler.torrent_db.update(torrent)











settings = read_settings_file("./settings/settings.json")
announce_handler = main_loop(settings, torrent_handler)
thread_handler = ThreadHandler(threading.current_thread(), None, announce_handler, None, None) # None is the udp tcp threads
app = Flask(__name__)
app.config["SECRET_KEY"] = "df0331cefc6c2b9a5d0208a726a5d1c0fd37324feba25506"
thread_handler.start_threads()


@app.route("/edit_settings", methods=["GET", "POST"])
def edit_settings():
    if request.method == "GET":
        return jsonify(settings.asdict())

    update_settings(settings, request)

    return SUCCESS


@app.route('/get_available_clients', methods=["GET"])
def get_available_clients():
    return get_client_list(False)


@app.route("/torrents", methods=["POST"])
def ret_torrent_list():
    return jsonify([torrent_obj.asdict() for torrent_obj in torrent_handler.get_torrents()])


@app.route("/create_torrentx", methods=["GET", "POST"])
def create_torrentx():
    if request.method == "POST":
        return return_torrent_file(request)
        

    return render_template("create-torrentx-page.html")


@app.route("/add_torrent", methods=["GET", "POST"])
def add_torrent():
    if request.method == "POST":
        handle_torrent(request, torrent_handler)
        return redirect(url_for('homepage'))

    return render_template("add-torrent-files-page.html", default_download_path=settings.default_download_path)


@app.route("/", methods=["GET"])
def homepage():
    title = "bitTorrentX Project"
    page = render_template("main-page.html", title=title)
    return page


if __name__ == "__main__":
    app.run(port=12345, debug=False)
