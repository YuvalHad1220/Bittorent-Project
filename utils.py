"""
maximum piece size - 32MiB (last return). We want pieces to be as small as possible (starting from 256kb) yet we want the total torrent file to be smaller than 15Mib
https://www.reddit.com/r/torrents/comments/dzxfz1/2019_whats_ideal_piece_size/ 

NOTE: need to configure to use si\decimal method
"""
import pathlib
import random
import string
import requests
import re
import json

class torrent_types:
    started = "STARTED"
    downloading = "DOWNLOADING"
    uploading = "SEEDING"
    stopped = "STOPPED"
    cant_download = "CHALKED"
    udp = "UDP"
    tcp = "TCP"

class setting_types:
    si = "SI"
    iec = "IEC"

def fetch_versions():
    request = "https://github.com/qbittorrent/qBittorrent/tags"

    response = requests.get(request)
    content = response.text

    pattern = r"release-[0-9]\.[0-9]\.[0-9]"

    matches = re.findall(pattern, content)
    matches = list(set(matches))

    return matches

def as_peer_id_user_agent(match):
    x, y, z = match.split("-")[1].split(".")
    peer_id = "-qB" + x + y + z + "-"
    user_agent = "qBittorrent/" + x + "." + y + "." + z

    return peer_id, user_agent


sizes = {
    "b": 1,
    "Kib": 1024,
    "Mib": 1024**2,
    "Gib": 1024**3,
    "Tib": 1024**4,
    "KiB": 1024 * 8,
    "MiB": 1024**2 * 8,
    "GiB": 1024**3 * 8,
    "TiB": 1024**4 * 8,
}

def rand_str(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))



def get_home_directory():
    return pathlib.Path.home()
def get_cwd_directory():
    return pathlib.Path.cwd()
def load_file(filename, _type):
    path = pathlib.Path(filename)
    if not path.exists():
        return None
    with open(path, _type) as f:
        return f.read()

def write_to_file(filename, _type, content):
    with open(pathlib.Path(filename), _type) as f:
        f.write(content)

def return_path(filename):
    path = pathlib.Path(filename)
    if not path.exists():
        path.mkdir()
    return path
    
def pieces_list_from_bytes(pieces_bytes: bytes):
    piece_size = 20 # each SHA-1 hash is 20 bytes
    pieces = [pieces_bytes[i:i+piece_size] for i in range(0, len(pieces_bytes), piece_size)]
    return pieces




def return_piece_size(file_size):
    piece_sizes = [
        256 * sizes["Kib"],
        512 * sizes["Kib"],
        1 * sizes["Mib"],
        2 * sizes["Mib"],
        4 * sizes["Mib"],
        8 * sizes["Mib"],
        16 * sizes["Mib"],
    ]

    for size in piece_sizes:
        # we want MiB not Mib
        if file_size / size < 5 * sizes["MiB"]:
            return {"size": size}

    return {"size": 32 * sizes["Mib"]}

def get_client_list(reload = False):
    versions = load_file("versions.json", "r")
    if not versions or reload:
        to_ret = fetch_versions()
        write_to_file("versions.json", "w", json.dumps(to_ret))
        return [as_peer_id_user_agent(match) for match in to_ret]


    versions = json.loads(versions)
    return [as_peer_id_user_agent(match) for match in versions]
    