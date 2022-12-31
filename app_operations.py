from flask import Request
from torrent import create_torrent
from utils import create_if_path_not_exists
from torrent_handler import TorrentHandler
def handle_torrent(request: Request, torrent_handler: TorrentHandler):
    download_path = request.form['downloadPath']
    to_decrypt = True if request.form['toDecrypt'] == 'True' else False
    save_file_path = 'added_torrent_files'
    torrent_files = request.files.getlist('torrent_files')

    # iterate over each file. create it, add to torrent_handler, save file
    for torrent_file in torrent_files:
        content = torrent_file.read()
        torrent_obj = create_torrent(save_file_path, content, download_path, to_decrypt)
        torrent_handler.add_torrent(torrent_obj)