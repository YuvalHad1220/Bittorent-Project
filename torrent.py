from dataclasses import dataclass, field
import math
from typing import List
from bencoding import decode, encode
from utils import torrent_types as types
import hashlib

@dataclass
class TorrentConnectionInfo:
    announce_url: str
    state: str
    time_to_announce: int = 0
    seeders: int = 0
    connected_seeders: int = 0
    leechers: int = 0
    connected_leechers: int = 0
    index: int = 0

    @property
    def tracker_type(self):
        if "udp" in self.announce_url:
            return types.udp
        return types.tcp
    
    

@dataclass
class File:
    path_name: str
    size_in_bytes: int
    first_piece_index: int = 0
    last_piece_index: int = 0
    index: int = 0

@dataclass
class Torrent:
    name: str
    info_hash: bytes
    file_path: str
    download_path: str
    metadata: bytes
    is_torrentx: bool
    connection_info: TorrentConnectionInfo
    files: List[File]
    piece_size_in_bytes: int
    pieces_hashes: bytes

    peers: List[str] = field(default_factory=list)
    downloaded: int = 0
    uploaded: int = 0
    
    index: int = 0

    @property
    def pieces_hashes_list(self):
        return [self.pieces_hashes[i:i+20] for i in range(0, len(self.pieces_hashes), 20)]

    @property
    def size(self):
        return sum(map(lambda x: x.size_in_bytes, self.files))

    @property
    def progress(self):
        p = (self.downloaded / self.size) * 100
        return round(p, 2)
    def asdict(self) -> dict:
        return {
            "index": self.index,
            "name": self.name,
            "state": self.connection_info.state,
            "type": "torrentx" if self.is_torrentx else "torrent",
            "tracker protocol": self.connection_info.tracker_type,
            "size": self.size,
            "download_speed": 0,
            "downloaded": self.downloaded,
            "upload_speed": 0,
            "uploaded": self.uploaded,
            "seeders": self.connection_info.seeders,
            "leechers": self.connection_info.leechers,
            "connected_seeders": self.connection_info.connected_seeders,
            "connected_leechers": self.connection_info.connected_leechers
        }


def create_files_path(info_decoded, piece_size) -> List[File]:
    file_list = []
    i = 0
    for entry in info_decoded[b'files']:
        print(entry)
        path = b'/'.join(entry[b'path']).decode()
        size = entry[b'length']
        piece_start_index = i
        piece_last_index = math.ceil(size / piece_size) + i
        i = piece_last_index + 1
        file_list.append(File(path, size, piece_start_index, piece_last_index))

    return file_list


def create_torrent(torrent_file_path, torrent_file_bytes, download_path):
    decoded: dict = decode(torrent_file_bytes)[0]
    announce = decoded.pop(b'announce').decode()
    info = decoded.pop(b'info')
    torrent_hash = hashlib.sha1(encode(info)).digest()
    name = info[b'name'].decode()
    piece_size = info[b'piece length']
    # pieces_list = pieces_list_from_bytes(info[b'pieces'])
    pieces = info[b'pieces']
    metadata = encode(decoded)
    is_torrentx = b'torrentx' in decoded
    # if multiple files - than we push a list that is filled with dicts such as {b'length: int, b'path: list[path]}
    if b'files' in info:
        file_list = create_files_path(info, piece_size)
    else:
        file_list = create_files_path({b'files': [{b'length': info[b'length'],b'path': [info[b'name']]}]}, piece_size)
    
    connection_info_obj = TorrentConnectionInfo(announce, types.wait_to_start)

    return Torrent(name, torrent_hash, torrent_file_path, download_path, metadata, is_torrentx, connection_info_obj, file_list, piece_size, pieces)