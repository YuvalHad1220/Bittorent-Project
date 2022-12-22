"""
Instead of taking care of torrent handling (getting sorted list, adding torrent to list and database, remove from list and database etc)
we will create a torrent handler that will take care of that in every operation
"""

class torrentHandler:
    def __init__(self) -> None:
        self.torrent_db = None
        self.torrent_list = None

    def add_torrent(self):
        pass

    def delete_torrent(self):
        pass

    def get_torrent_list(self):
        pass

    def get_torrents_by_index(self, *indexes):
        pass

    def get_sorted_torrent_copy(self, sort_by):
        pass


    def save_torrents_to_db(self):
        pass