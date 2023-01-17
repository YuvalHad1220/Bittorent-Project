from flask import Flask, render_template, request, jsonify, redirect, url_for
from settings.settings import read_settings_file
from app_operations import *
from database.torrent_handler import TorrentHandler
from utils import get_client_list, announce_types
import asyncio
from connection_handlers.peers_request_handler import connect_to_single_peer
from connection_handlers.trakcer_request_handler import announce_http_legacy, announce_udp_legacy
SUCCESS = {"success": True}
FAILURE = {"success": False}

torrent_handler = TorrentHandler("./database/torrent.db")
settings = read_settings_file("./settings/settings.json")
app = Flask(__name__)
app.config["SECRET_KEY"] = "df0331cefc6c2b9a5d0208a726a5d1c0fd37324feba25506"

if __name__ == "__main__":
    udp_torrent = torrent_handler.get_torrents()[0]
    assert udp_torrent.connection_info.tracker_type == "UDP"
    res = asyncio.run(announce_udp_legacy(udp_torrent, announce_types.start, settings))

    # tcp_torrent = torrent_handler.get_torrents()[1]
    # assert tcp_torrent.connection_info.tracker_type == "TCP"

    # res = asyncio.run(announce_http_legacy(tcp_torrent, announce_types.start, settings))
    peer_list = res[3]
    asyncio.run(connect_to_single_peer(udp_torrent, peer_list, settings))

@app.route("/edit_settings", methods = ["GET", "POST"])
def edit_settings():
    if request.method == "GET":
        return jsonify(settings.asdict())

    update_settings(settings, request)
    
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
        return redirect(url_for('homepage'))
        

    return render_template("add-torrent-files-page.html", default_download_path = settings.default_download_path)


@app.route("/", methods=["GET"])
def homepage():
    title = "my torrent project"
    page = render_template("main-page.html", title=title)
    return page

if __name__ == "__main__":
    app.run(port=12345, debug=False)
