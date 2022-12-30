from dataclasses import dataclass, asdict, field
from typing import List
from bencoding import decode, encode
from utils import pieces_list_from_bytes

class types:
    downloading = "DOWNLOADING"
    uploading = "SEEDING"
    stopped = "STOPPED"
    cant_download = "CHALKED"
    udp = "UDP"
    tcp = "TCP"


@dataclass
class TorrentConnectionInfo:
    announce_url: str
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
class Torrent:
    name: str
    size: int
    is_torrentx: bool
    file_path: str
    download_path: str
    metadata: bytes
    piece_info: Pieces
    connection_info: TorrentConnectionInfo
    peers: List[Peer] = field(default_factory=list)
    downloaded: int = 0
    uploaded: int = 0
    index: int = 0

    # in final project this will be replaced with custom asdict
    def asdict(self) -> dict:
        return asdict(self)


def create_torrent(torrent_file_path, torrent_file_bytes, download_path, to_dcrypt):
    decoded: dict = decode(torrent_file_bytes)[0]
    announce = decoded.pop(b'announce').decode()
    info = decoded.pop(b'info')
    name = info[b'name'].decode()
    size = info[b'length']
    piece_size = info[b'piece length']
    pieces_list = pieces_list_from_bytes(info[b'pieces'])
    metadata = encode(decoded)
    is_torrentx = b'torrentx' in decoded
    pieces_obj = Pieces(piece_size, pieces_list)
    connection_info_obj = TorrentConnectionInfo(announce)
    return Torrent(name, size, is_torrentx, torrent_file_path,  download_path, metadata, pieces_obj, connection_info_obj)
