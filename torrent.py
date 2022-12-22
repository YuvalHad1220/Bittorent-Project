from dataclasses import dataclass, asdict

@dataclass
class torrent:
    index: int = 1
    name: str = "Yuval's bestest torrent client"
    state: str = "Downloading"
    _type: str = "torrentx"
    protocol: str = "UDP"
    size: int = 234234324
    downloaded: int = 3242
    download_speed: int = 213
    uploaded: int = 2
    upload_speed: int = 1
    seeders: int = 1003
    connected_seeders: int = 3
    leechers: int = 13
    connected_leechers: int = 0

    # in final project this will be replaced with custom asdict
    def asdict(self) -> dict:
        return asdict(self)
    