from database.dctodb import dctodb
from torrent import Torrent
from utils import sort_types


"""
Instead of taking care of torrent handling (getting sorted list, adding torrent to list and database, remove from list and database etc)
we will create a torrent handler that will take care of that in every operation
"""


class TorrentHandler:
    def __init__(self, db_filename) -> None:
        self.torrent_db = dctodb(Torrent, db_filename)
        self.torrent_list: list[Torrent] = self.torrent_db.fetch_all()

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
        return self.torrent_list

    def get_torrents_by_index(self, *indexes):
        pass

    def get_sorted_torrent_copy(self, sort_by):
        match sort_by:
            case sort_types.name:
                return sorted(self.torrent_list, key=lambda x: x.name)

            case sort_types.state:
                return sorted(self.torrent_list, key=lambda x: x.connection_info.state)
            case sort_types.type:
                return sorted(self.torrent_list, key=lambda x: x.is_torrentx)

            case sort_types.tracker_protocol:
                return sorted(self.torrent_list, key=lambda x: x.connection_info.tracker_type)

            case sort_types.size:
                return sorted(self.torrent_list, key=lambda x: x.size)

            case sort_types.progress:
                return sorted(self.torrent_list, key=lambda x: x.progress)

            case sort_types.download_speed:
                return sorted(self.torrent_list, key=lambda x: x.connection_info.download_speed)

            case sort_types.downloaded:
                return sorted(self.torrent_list, key=lambda x: x.downloaded)

            case sort_types.upload_speed:
                return sorted(self.torrent_list, key=lambda x: x.connection_info.upload_speed)

            case sort_types.uploaded:
                return sorted(self.torrent_list, key=lambda x: x.uploaded)

            case sort_types.leechers:
                return sorted(self.torrent_list, key=lambda x: x.connection_info.leechers)

            case sort_types.seeders:
                return sorted(self.torrent_list, key=lambda x: x.connection_info.seeders)

            case _:
                return self.torrent_list

            

    def save_torrents_to_db(self):
        pass

    

