"""
Will handle announcements to the tracker weather its via http requests or udp.

1. Identify type of torrent (torrentx, torrent)
2. Identify tracker type (http, udp)
3. get peers
4. start downloading


if already downloading:
    1. update

if finished:
    1. update
    2. change state to uploading




"""
import aiohttp
from torrent import Torrent
from settings.settings import Settings
from database.torrent_handler import TorrentHandler
from typing import List
from utils import rand_str
import struct
import socket
import requests
PROT_ID = 0x41727101980
# A thread should start that def:
async def main(torrent_handler: TorrentHandler):
    torrent_list = torrent_handler.get_torrents()



# splits announcements to torrentx(supports multiple announcements at once) and regular torrent files
def _split_torrentx_regular(to_announce_list):
    pass

# splits announcements to udp and http trackers. both torrentx and regular can support both
def _split_udp_http(to_announce_list):
    pass


"""
All of these function should reduce to a couple of functions: announce_udp, announce_http, announce_multiple_udp, announce_multiple_http
"""

async def announce_start_http(aiohttp_client: aiohttp.ClientSession, *torrents: List[Torrent]):
    pass

async def _announce_legacy_start_http(torrent: Torrent, settings: Settings):
    HTTP_HEADERS = {
        "Accept-Encoding": "gzip",
        "User-Agent": settings.user_agent
    }

    HTTP_PARAMS = {
        "info_hash": torrent.info_hash,
        "peer_id": settings.peer_id + settings.rand_id,
        "port": settings.port,
        "uploaded": torrent.uploaded,
        "downloaded": torrent.downloaded,
        "left": torrent.size - torrent.downloaded,
        "event": "started",
        "compact": 1,
        "numwant": 200,
        "supportcrypto": 1,
        "no_peer_id": 1
    }

    res = requests.get(url= torrent.announce_url, headers = HTTP_HEADERS)
    print(res)


def _announce_to_struct_udp_legacy(event, torrent: Torrent, settings: Settings, conn_id, trans_id):
    if event == "start":
        event_param = 2

    peer_id = settings.user_agent + settings.random_id

    peer_id = peer_id.encode()

    key = 1234

    # 8 bytes conn_id
    # 4 bytes action. will be 1 for announce
    # 4 bytes trans_id
    # 20 byte array of info hash
    # 20 bytes peer_id
    # 8 bytes downloaded
    # 8 bytes left
    # 8 bytes uploaded
    # 4 bytes event 
    # 4 bytes ip (0 to use sender id)
    # 4 bytes random key
    # 4 bytes numwant (-1 for client to decide)
    # 2 bytes port were listening on
    # 4 bytes extenstions
    # 1 byte padding

    return struct.pack("! q i 4s 20s 20s q q q i i i i H x",
                     conn_id, 1, trans_id, torrent.info_hash, peer_id,
                     torrent.downloaded, torrent.size - torrent.downloaded, torrent.uploaded event_param, 0, key, -1, settings.port, 0)

def unpack_start_announce_struct_data(message):
     # 4 bytes action
     # 4 bytes trans_id
     # 4 bytes interval
     # 4 bytes leechers
     # 4 byte seeders

    message = message[:20]

    return struct.unpack("! i 4s i i i", message)

def unpack_start_announce_peers(message):
    message = message[20:] # first 20 bytes are tracker related- rest are peers

    # each peer is 6 bytes: 4 bytes ip, 2 bytes port 
    peer_list = [message[i:i+6] for i in range(0, len(message), 6)]
    peer_list_str = []
    for peer_data in peer_list:
        ip, port = struct.unpack('! 4s H', peer_data)
        ip = socket.inet_ntoa(ip)

        peer_list_str.append((ip, port))

    return peer_list_str


def announce_legacy_start_udp(torrent: Torrent, settings: Settings):
    # first we will pack our data: 
    # 8 bytes protocol id
    # 4 bytes action
    # 4 bytes transaction id
    # 1 empty byte
    # if no response is recieved after 15 secs, we try again until 1 minute since beginning. then we just give up (need to implement)
    action = 0  # Connect action
    trans_id = settings.random_id[:4].encode()
    message = struct.pack("! q l 4s x", PROT_ID, action, trans_id)

    announce_data = torrent.connection_info.announce_url
    announce_data = announce_data.replace("udp://","")
    announce_url, port = announce_data.split(":")
    port = int(port)
    addr = (announce_url, port)

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.sendto(message, addr)
    response, addr = udp_socket.recvfrom(128)

    # response should be:
    # 4 bytes action (value 0 since we just connected)
    # 4 byts same trans_id
    # 8 bytes conn_id
    action_recv, trans_id_recv, conn_id = struct.unpack("! l 4s q", response)
    if trans_id_recv != trans_id and action_recv != action:
        raise "ERROR"
        
    message = _announce_to_struct_udp_legacy("start", torrent, settings, conn_id, trans_id,)
    print(message)
    udp_socket.sendto(message, addr)
    response, addr = udp_socket.recvfrom(1024)
    # now we need to construct our announcing data
    data = unpack_start_announce_struct_data(response)
    peer_list = unpack_start_announce_peers(response)

    print(data, peer_list)

async def _announce_legacy_resume_http():
    pass

async def _announce_legacy_resume_udp():
    pass

async def _announce_legacy_finish_http():
    pass

async def _announce_legacy_finish_udp():
    pass

async def announce_start_udp(*instances):
    pass

async def announce_resume_http(aiohttp_client,*instances):
    pass

async def announce_resume_udp(*instances):
    pass

async def announce_finish_http(aiohttp_client,*instances):
    pass

async def announce_finish_udp(*instances):
    pass