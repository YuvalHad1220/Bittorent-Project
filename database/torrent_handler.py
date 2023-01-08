from database.dctodb import dctodb
from torrent import Torrent

"""
Instead of taking care of torrent handling (getting sorted list, adding torrent to list and database, remove from list and database etc)
we will create a torrent handler that will take care of that in every operation
"""


class TorrentHandler:
    def __init__(self, db_filename) -> None:
        self.torrent_db = dctodb(Torrent, db_filename)
        self.torrent_list = self.torrent_db.fetch_all()

    def add_torrent(self, torrent_obj: Torrent):
        old_index = torrent_obj.index

        self.torrent_db.insert_one(torrent_obj)

        if old_index != torrent_obj.index:
            self.torrent_list.append(torrent_obj)
            return True
        return False

    def delete_torrent(self):
        pass

    def get_torrents(self):
        return self.torrent_list[:]

    def get_torrents_by_index(self, *indexes):
        pass

    def get_sorted_torrent_copy(self, sort_by):
        pass

    def save_torrents_to_db(self):
        pass


