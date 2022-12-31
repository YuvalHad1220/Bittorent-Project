from torrent import Torrent
from bencoding import *
import pprint
download_path = "download_folder"
torrent_file_path = "test.torrent"
stored_file_path = "added_torrents"
to_decrypt = False

with open(torrent_file_path, 'rb') as f:
    content = f.read()

decoded = decode(content)[0]
print(decoded.keys)

# create_torrent(torrent_file_path, content, download_path, to_decrypt)