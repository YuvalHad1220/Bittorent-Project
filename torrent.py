from dataclasses import dataclass, asdict
from typing import List
@dataclass
class torrent_pieces:
    @classmethod
    def create(cls, pieces_bytes: bytes):
        piece_size = 20 # each SHA-1 hash is 20 bytes
        pieces = [pieces_bytes[i:i+piece_size] for i in range(0, len(pieces_bytes), piece_size)]
        return pieces

    index: int
    piece_length: int
    pieces: List[bytes] # will contain a list where each item is 20 bytes


@dataclass
class torrent_temp_info:
    seeders: int = 1003
    connected_seeders: int = 3
    leechers: int = 13
    connected_leechers: int = 0
    upload_speed: int = 1
    download_speed: int = 213

@dataclass
class torrent:
    index: int
    name: str
    state: str
    _type: str
    protocol: str
    size: int
    downloaded: int
    uploaded: int
    pieces: torrent_pieces
    connection_info: torrent_temp_info
    pieces: torrent_pieces 

    # in final project this will be replaced with custom asdict
    def asdict(self) -> dict:
        return asdict(self)
