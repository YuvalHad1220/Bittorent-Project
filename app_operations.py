from flask import Request
from torrent import create_torrent
from utils import return_path
from torrent_handler import TorrentHandler
import os
from utils import create_torrent_file_from_directory, create_torrent_file_from_single_file
def handle_torrent(request: Request, torrent_handler: TorrentHandler):
    download_path = request.form['downloadPath']
    save_file_path = 'added_torrent_files'
    torrent_files = request.files.getlist('torrent_files')

    # iterate over each file. create it, add to torrent_handler, save file
    for torrent_file in torrent_files:
        content = torrent_file.read()
        torrent_file.close()
        
        torrent_obj = create_torrent(save_file_path, content, download_path)
        if not torrent_handler.add_torrent(torrent_obj):
            raise Exception("Error in adding torrent. error is in app_operations.py")

        with open(return_path(save_file_path) / torrent_file.filename, 'wb') as f:
            f.write(content)

            
def update_settings(settings_obj, request):
    results = request.get_json()
    results['download_torrentx_encryption'] = True if results['download_torrentx_encryption'] == 'True' else False
    settings_obj.update_settings(**results)


def return_torrent_file(request):
        torrent_name = request.form['torrent_name']
        piece_size = int(request.form['piece_size'])
        trackers = request.form['trackers'].split('\n')
        comments = request.form['comments']
        filepath = request.form['file_path']
        # Process the form data as needed

        if os.path.isfile(filepath):
            return create_torrent_file_from_single_file(piece_size, filepath, torrent_name, comments, trackers)

        else:
            return create_torrent_file_from_directory(piece_size, filepath, torrent_name, comments, trackers)
