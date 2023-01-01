from dataclasses import dataclass, field
from typing import List
from bencoding import decode, encode
from utils import pieces_list_from_bytes
from utils import torrent_types as types


@dataclass
class TorrentConnectionInfo:
    announce_url: str
    state: str
    seeders: int = 0
    connected_seeders: int = 0
    leechers: int = 0
    connected_leechers: int = 0
    upload_speed: int = 0
    download_speed: int = 0
    index: int = 0

    @property
    def tracker_type(self):
        if "udp" in self.announce_url:
            return types.udp
        return types.tcp
    
@dataclass
class Peer:
    ip: str
    index: int = 0

@dataclass
class Pieces:
    piece_size: int
    pieces_hashes: List[bytes]
    index: int = 0

@dataclass
class File:
    path_name: str
    size: int
    index: int = 0

@dataclass
class Torrent:
    name: str
    file_path: str
    download_path: str
    auto_decrypt: bool
    metadata: bytes
    is_torrentx: bool
    pieces_info: Pieces
    connection_info: TorrentConnectionInfo
    files: List[File]
    peers: List[Peer] = field(default_factory=list)
    downloaded: int = 0
    uploaded: int = 0
    index: int = 0

    @property
    def size(self):
        return sum(map(lambda x: x.size, self.files))

    # in final project this will be replaced with custom asdict
    def asdict(self) -> dict:
        return {
            "index": self.index,
            "name": self.name,
            "state": self.connection_info.state,
            "type": "torrentx" if self.is_torrentx else "torrent",
            "tracker protocol": self.connection_info.tracker_type,
            "size": self.size,
            "download_speed": self.connection_info.download_speed,
            "downloaded": self.downloaded,
            "upload_speed": self.connection_info.upload_speed,
            "uploaded": self.uploaded,
            "seeders": self.connection_info.seeders,
            "leechers": self.connection_info.leechers,
            "connected_seeders": self.connection_info.connected_seeders,
            "connected_leechers": self.connection_info.connected_leechers
        }


def create_files_path(info_decoded) -> List[File]:
    file_list = []
    for entry in info_decoded[b'files']:
        size = entry[b'length']
        path = b'/'.join(entry[b'path']).decode()
        file_list.append(File(path, size))

    return file_list


def create_torrent(torrent_file_path, torrent_file_bytes, download_path, to_decrypt):
    decoded: dict = decode(torrent_file_bytes)[0]
    announce = decoded.pop(b'announce').decode()
    info = decoded.pop(b'info') 

    # if multiple files - than we push a list that is filled with dicts such as {b'length: int, b'path: list[path]}
    if b'files' in info:
        file_list = create_files_path(info)
    else:
        file_list = create_files_path({b'files': [{b'length': info[b'length'],b'path': [info[b'name']]}]})
    

    
    name = info[b'name'].decode()
    piece_size = info[b'piece length']
    pieces_list = pieces_list_from_bytes(info[b'pieces'])
    metadata = encode(decoded)
    is_torrentx = b'torrentx' in decoded
    pieces_obj = Pieces(piece_size, pieces_list)

    connection_info_obj = TorrentConnectionInfo(announce, types.started)
    return Torrent(name, torrent_file_path, download_path, to_decrypt, metadata, is_torrentx, pieces_obj, connection_info_obj, file_list)