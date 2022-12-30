from torrent import create_torrent, Torrent
import dctodb


download_path = "download_folder"
torrent_file_path = "manjaro-kde-21.3.7-220816-linux515.iso.torrent"
stored_file_path = "added_torrents"
to_decrypt = False
with open(torrent_file_path, 'rb') as f:
    content = f.read()


torrent_obj = create_torrent(stored_file_path, content, download_path, to_decrypt)

torrent_db = dctodb.dctodb(Torrent, "test.db")
torrent_db.insert_one(torrent_obj)