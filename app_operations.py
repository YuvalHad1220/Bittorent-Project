from flask import Request
from torrent import create_torrent
from utils import return_path
from torrent_handler import TorrentHandler
def handle_torrent(request: Request, torrent_handler: TorrentHandler):
    download_path = request.form['downloadPath']
    to_decrypt = True if request.form['toDecrypt'] == 'True' else False
    save_file_path = 'added_torrent_files'
    torrent_files = request.files.getlist('torrent_files')

    # iterate over each file. create it, add to torrent_handler, save file
    for torrent_file in torrent_files:
        content = torrent_file.read()
        torrent_file.close()
        
        torrent_obj = create_torrent(save_file_path, content, download_path, to_decrypt)
        if not torrent_handler.add_torrent(torrent_obj):
            raise Exception("Error in adding torrent. error is in app_operations.py")

        with open(return_path(save_file_path) / torrent_file.filename, 'wb') as f:
            f.write(content)
