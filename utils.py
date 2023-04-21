"""
maximum piece size - 32MiB (last return). We want pieces to be as small as possible (starting from 256kb) yet we want the total torrent file to be smaller than 15Mib
https://www.reddit.com/r/torrents/comments/dzxfz1/2019_whats_ideal_piece_size/ 

NOTE: need to configure to use si\decimal method
"""
import hashlib
import os
import pathlib
import random
import string
import time

import requests
import urllib
import re
import json

import bencoding

from flask import  make_response


class sort_types:
    index = "INDEX"
    name = "NAME"
    state = "STATE"
    type = "TYPE"
    tracker_protocol = "TRACKER_PROTOCOL"
    size = "SIZE"
    progress = "PROGRESS"
    download_speed = "DOWNLOAD_SPEED"
    downloaded = "DOWNLOADED"
    upload_speed = "UPLOAD_SPEED"
    uploaded = "UPLOADED"
    seeders = "SEEDERS"
    leechers = "LEECHERS"


class torrent_types:
    wait_to_start = "WAITING START"
    wait_to_finish = "WAITING FINISH"
    finished = "FINISHED"
    started = "STARTED"
    downloading = "DOWNLOADING"
    uploading = "SEEDING"
    stopped = "STOPPED"
    cant_download = "CHALKED"
    udp = "UDP"
    tcp = "TCP"


class msg_types:
    choke = 0
    unchoke = 1
    interested = 2
    notinterested = 3
    have = 4
    bitfield = 5
    request = 6
    piece = 7
    cancel = 8


# # a list but we will look at it like a dict where each index is a key
# msg_dict = list(msg_types.__dict__.keys())

class announce_types:
    start = "START"
    finish = "FINISH"
    resume = "RESUME"
    stop = "STOP"


class settingtypes:
    si = "SI"
    iec = "IEC"


def print_bytes_as_bits(bytes_arr):
    print(''.join(['{:08b}'.format(b) for b in bytes_arr]))


def create_torrent_file_from_directory(piece_size, root_path, comments = None):
    # Create a list to hold the file dictionaries
    files = []
    pieces_list = []
    # Get the root directory name
    root_dirname = os.path.basename(root_path)
    # Iterate over each file in the root directory
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Create a list to hold the file dictionaries for this directory
        dir_files = []
        # Iterate over each file in the directory
        for filename in filenames:
            # Get the full path to the file
            filepath = os.path.join(dirpath, filename)
            # Get the file size
            filesize = os.path.getsize(filepath)
            # Calculate the SHA1 hash of the file
            sha1 = hashlib.sha1()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(piece_size), b""):
                    sha1.update(chunk)
            # Add the file dictionary to the list
            dir_files.append({
                "path": [os.path.relpath(filepath, root_path)],
                "length": filesize,
            })
            pieces_list.append(sha1.digest())
        # Add the directory dictionary to the files list
        if dir_files:
            files.append({
                "path": [os.path.relpath(dirpath, root_path)],
                "files": dir_files
            })
    # Create the main dictionary
    torrent = {
        "info": {
            "name": root_dirname,
            "piece length": piece_size,
            "files": files,
            "pieces": b''.join(pieces_list)
        },
        "creation date": int(time.time()),
        "created by": "My BitTorrent Client",
    }
    # Encode the dictionary as bencoded data

    if comments:
        torrent['comments'] = comments

    # Write the torrent file
    encoded = bencoding.encode(torrent)
    response = make_response(encoded)

    # Set the appropriate headers
    response.headers.set('Content-Type', 'application/x-bittorrent')
    response.headers.set('Content-Disposition', 'attachment', filename=f"{os.path.basename(root_path)}.torrent")

    return response

def create_torrent_file_from_single_file(piece_size, root_path, comments = None):
    torrent = {
        'info': {
            'name': os.path.basename(root_path),
            'piece length': piece_size,
            'length': os.path.getsize(root_path),
            'pieces': b'',
        },
        'creation date': int(time.time()),
        'created by': 'bitTorrentX/0.1b',
        'torrentx': ''  # that just symbolizes that we are a torrent x
    }

    if comments:
        torrent['comments'] = comments

    # Read the file and generate piece hashes
    with open(root_path, 'rb') as f:
        while True:
            piece = f.read(torrent['info']['piece length'])
            if not piece:
                break
            torrent['info']['pieces'] += hashlib.sha1(piece).digest()

    # Write the torrent file
    encoded = bencoding.encode(torrent)

    # Set the appropriate headers
    response = make_response(encoded)
    # Set the appropriate headers
    response.headers.set('Content-Type', 'application/x-bittorrent')
    response.headers.set('Content-Disposition', 'attachment', filename=f"{os.path.basename(root_path)}.torrent")

    return response


# create_torrent_file_from_single_file(16384, r"C:\Users\Yuval
# Hadar\Desktop\Bittorent-My_Project\tests\test.torrent", "test.torrent")
# create_torrent_file_from_directory(16, r"C:\Users\Yuval Hadar\Desktop\mcserver", "")


# since aiohttp doesnt support sending sha-1 hashes, we encode it properly ourselves
# we return the params and the headers as just headers
def encode_params_with_url(params_dict, url):
    params = urllib.parse.urlencode(params_dict)
    params = params.replace("%25", "%")
    return f"{url}?{params}"


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
    peer_id = "-qB" + x + y + z + "0-"
    user_agent = "qBittorrent/" + x + "." + y + "." + z

    return peer_id, user_agent


sizes = {
    "b": 1,
    "Kib": 1024,
    "Mib": 1024 ** 2,
    "Gib": 1024 ** 3,
    "Tib": 1024 ** 4,
    "KiB": 1024 * 8,
    "MiB": 1024 ** 2 * 8,
    "GiB": 1024 ** 3 * 8,
    "TiB": 1024 ** 4 * 8,
    "KB": 1000,
    "MB": 1000 ** 2,
    "GB": 1000 ** 3
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
    piece_size = 20  # each SHA-1 hash is 20 bytes
    pieces = [pieces_bytes[i:i + piece_size] for i in range(0, len(pieces_bytes), piece_size)]
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


def get_client_list(reload=False):
    versions = load_file("versions.json", "r")
    if not versions or reload:
        to_ret = fetch_versions()
        write_to_file("versions.json", "w", json.dumps(to_ret))
        return [as_peer_id_user_agent(match) for match in to_ret]

    versions = json.loads(versions)
    return [as_peer_id_user_agent(match) for match in versions]
