from dctodb import dctodb
from torrent import Torrent
import time

"""
Instead of taking care of torrent handling (getting sorted list, adding torrent to list and database, remove from list and database etc)
we will create a torrent handler that will take care of that in every operation
"""


class TorrentHandler:

    def __init__(self, db_filename) -> None:
        self.torrent_db = dctodb(Torrent, db_filename)
        self.torrent_list: list[Torrent] = self.torrent_db.action_to_db(self.torrent_db.fetch_all)

    def add_torrent(self, torrent_obj: Torrent):
        old_index = torrent_obj.index

        self.torrent_db.action_to_db(self.torrent_db.insert_one, torrent_obj)

        if old_index != torrent_obj.index:
            self.torrent_list.append(torrent_obj)
            return True
        return False

    def delete_torrent(self, torrent_obj):
        self.torrent_list.remove(torrent_obj)
        self.torrent_db.action_to_db(self.torrent_db.delete, torrent_obj)


    def get_torrents(self):
        return self.torrent_list

    def update(self):
        self.torrent_db.action_to_db(self.torrent_db.update, *self.torrent_list)

    def update_loop(self):
        print("started io thread")
        time.sleep(60)
        self.torrent_db.action_to_db(self.torrent_db.update, *self.torrent_list)
        print("updated torrents in db")

        while True:
            time.sleep(60)
            print("updated torrents in db")



if __name__ == "__main__":
    torrent_handler = TorrentHandler("torrent.db")
    torrents = torrent_handler.get_torrents()
    torrents[0].download_path = "dsf"
    torrents[0].connection_info.announce_url = "nothing"
    torrents[0].peers += ["wannasfsd:132434234", "lolrr:1dd23123"]

    torrent_handler.torrent_db.update(torrents[0])
    print(torrents[0])
    # torrent_handler.update()