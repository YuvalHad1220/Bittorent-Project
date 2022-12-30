from flask import Request
from utils import create_if_path_not_exists
def handle_torrent(request: Request):
    directory = request.form['downloadPath']
    auto_decrypt = request.form['toDecrypt']
    torrent_files = request.files.getlist('torrent_files')

    # iterate over each file. create it, add to torrent_handler, save file
    for torrent_file in torrent_files:
        
        pass
