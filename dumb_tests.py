from torrent import create_torrent
from torrent_handler import TorrentHandler
from bencoding import *
download_path = "download_folder"
torrent_file_path = "test.torrent"
stored_file_path = "added_torrents"
to_decrypt = False


handler = TorrentHandler('torrent.db')

