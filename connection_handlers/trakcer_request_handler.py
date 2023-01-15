from torrent import Torrent
from typing import List
import aioudp
import asyncio
from settings.settings import Settings
import struct
import requests
from bencoding import decode
import socket
PROT_ID = 0x41727101980


def split_torrent_list(torrent_list: List[Torrent]):
    udp_torrents = []
    http_torrents = []

    for torrent in torrent_list:
        if "udp://" in torrent.connection_info.announce_url:
            udp_torrents.append(torrent)
        else:
            http_torrents.append(torrent)

    return udp_torrents, http_torrents


async def udp_loop(udp_torrents_list):
    pass


async def http_loop(http_torrents_list):
    pass

async def main_loop(torrent_list):

    udp_torrents , http_torrents = split_torrent_list()

    # udp_torrents_legacy, udp_torrentx = 
    # http_torrents_legacy, http_torrentsx = 
    
    udp_torrents_loop = asyncio.create_task(udp_loop(udp_torrents))
    http_torrents_loop = asyncio.create_task(http_loop(http_torrents))
    await asyncio.gather(udp_torrents_loop, http_torrents_loop)



ANNOUNCE_TABLE_HTTP = {
    "START": "started",
    "RESUME": None,
    "STOP": "stopped",
    "FINISH": "completed"
}

ANNOUNCE_TABLE_UDP = {
    "START": 2,
    "RESUME": 0,
    "FINISH": 1,
    "STOP": 3
}

def announce_http_legacy(torrent: Torrent, event: str, settings: Settings):
    HEADERS = {
        "Accept-Encoding": "gzip",
        "User-Agent": settings.peer_id,
    }

    PARAMS = {
        "info_hash": torrent.info_hash,
        "peer_id": settings.user_agent + settings.random_id,
        "port": settings.port,
        "uploaded": torrent.uploaded,
        "downloaded": torrent.downloaded,
        "left": torrent.size - torrent.downloaded,
        "compact": 1,
        "numwant": 200,
        "supportcrypto": 1,
        "no_peer_id": 1
    }

    if ANNOUNCE_TABLE_HTTP[event]:
        PARAMS["event"] = ANNOUNCE_TABLE_HTTP[event]

    res = requests.get(torrent.connection_info.announce_url, headers = HEADERS, params=PARAMS)
    res = res.content
    res = decode(res)[0]
    interval = res[b"interval"]

    peers = res[b"peers"]
    peer_list_str = [peers[i:i+6] for i in range(0, len(peers), 6)]
    peer_list = []
    for peer_data in peer_list_str:

        ip, port = struct.unpack('! 4s H', peer_data)
        ip = socket.inet_ntoa(ip)

        peer_list.append((ip, port))

    if b"incomplete" not in res:
        leechers = len(peer_list)
    else:
        leechers = res[b"incomplete"]

    if b"complete" not in res:
            seeders = 0
    else:
        seeders = res[b"complete"]

    return interval, leechers, seeders, peer_list

def build_announce_struct(torrent: Torrent, event: str, settings: Settings, conn_id, trans_id):

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

    return struct.pack("! q i 4s 20s 20s q q q i i i i H i x",
                     conn_id, 1, trans_id, torrent.info_hash, peer_id,
                     torrent.downloaded, torrent.size - torrent.downloaded, torrent.uploaded, ANNOUNCE_TABLE_UDP[event], 0, key, -1, settings.port, 0)

def parse_announce_resp_struct(message):
     # 4 bytes action
     # 4 bytes trans_id
     # 4 bytes interval
     # 4 bytes leechers
     # 4 byte seeders
    tracker_data = message[:20]
    action, trans_id, interval, leechers, seeders = struct.unpack("! i 4s i i i", tracker_data)

    peers_data = message[20:]
    peers_data = [peers_data[i:i+6] for i in range(0, len(peers_data), 6)]

    peer_list = []
    for peer_data in peers_data:
        ip, port = struct.unpack('! 4s H', peer_data)
        ip = socket.inet_ntoa(ip)

        peer_list.append((ip, port))


    return interval, leechers, seeders, peer_list

def build_conn_struct(settings: Settings):
    # 8 bytes protocol id
    # 4 bytes action
    # 4 bytes transaction id
    # 1 empty byte
    # if no response is recieved after 15 secs, we try again until 1 minute since beginning. then we just give up (need to implement)
    action = 0  # Connect action
    trans_id = settings.random_id[:4].encode()
    return struct.pack("! q l 4s x", PROT_ID, action, trans_id)

def vaildated_conn_id(message):
    # response should be:
    # 4 bytes action (value 0 since we just connected)
    # 4 byts same trans_id
    # 8 bytes conn_id
    action_recv, trans_id_recv, conn_id = struct.unpack("! l 4s q", message)

    return conn_id, trans_id_recv

async def init_conn(message, addr):
    remote_conn = await aioudp.open_remote_endpoint(*addr)

    remote_conn.send(message)
    data = await remote_conn.receive()
    return data, remote_conn

async def announce_udp_legacy(torrent: Torrent, event: str, settings: Settings):
    announce_data = torrent.connection_info.announce_url
    announce_data = announce_data.replace("udp://","")
    announce_url, port = announce_data.split(":")
    port = int(port)
    addr = (announce_url, port)

    init_conn_msg = build_conn_struct(settings)
    resp, remote_conn = await init_conn(init_conn_msg, addr)
    conn_id, trans_id = vaildated_conn_id(resp)
        
    message = build_announce_struct(torrent, event, settings, conn_id, trans_id)
    remote_conn.send(message)
    response = await remote_conn.receive()

    # now we need to construct our announcing data
    print( parse_announce_resp_struct(response))
    return parse_announce_resp_struct(response)

    














# async def announce_start_udp(*instances):
#     pass

# async def announce_resume_http(aiohttp_client,*instances):
#     pass

# async def announce_resume_udp(*instances):
#     pass

# async def announce_finish_http(aiohttp_client,*instances):
#     pass

# async def announce_finish_udp(*instances):
#     pass