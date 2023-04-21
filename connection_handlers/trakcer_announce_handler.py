from torrent import Torrent
from typing import List
import aioudp
import aiohttp
import asyncio
from settings.settings import Settings
import struct
from utils import encode_params_with_url, announce_types, torrent_types
from bencoding import decode
import socket
import logging

PROT_ID = 0x41727101980

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

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def split_torrent_list(torrent_list: List[Torrent]):
    udp_torrents = []
    http_torrents = []

    for torrent in torrent_list:
        if "udp://" in torrent.connection_info.announce_url:
            udp_torrents.append(torrent)
        else:
            http_torrents.append(torrent)

    return udp_torrents, http_torrents


async def udp_loop(udp_torrents_list, settings: Settings):
    to_announce = []
    for torrent in udp_torrents_list:
        print(torrent.connection_info.time_to_announce)

        if torrent.connection_info.state == torrent_types.wait_to_start:
            to_announce.append(announce_udp_legacy(torrent, announce_types.start, settings))

        elif torrent.connection_info.state == torrent_types.wait_to_finish:
            to_announce.append(announce_udp_legacy(torrent, announce_types.finish, settings))

        elif torrent.connection_info.time_to_announce == 0:
            to_announce.append(announce_udp_legacy(torrent, announce_types.resume, settings))

        torrent.connection_info.time_to_announce -= 1

    await asyncio.gather(*to_announce)


async def http_loop(http_torrents_list: List[Torrent], settings: Settings):
    to_announce = []
    # at every torrent we add, time to announce is also zero so if we dont continue it will perform same task twice; can also be the same at wait to finish and announce resume
    # so we will follow seder kdimuyot
    for torrent in http_torrents_list:
        print(torrent.connection_info.time_to_announce)
        if torrent.connection_info.state == torrent_types.wait_to_start:
            to_announce.append(announce_http_legacy(torrent, announce_types.start, settings))

        elif torrent.connection_info.state == torrent_types.wait_to_finish:
            to_announce.append(announce_http_legacy(torrent, announce_types.finish, settings))


        elif torrent.connection_info.time_to_announce == 0:
            to_announce.append(announce_http_legacy(torrent, announce_types.resume, settings))

        torrent.connection_info.time_to_announce -= 1

    await asyncio.gather(*to_announce)


async def main_loop(settings, torrent_handler):
    logging.debug("running tracker main loop")
    while True:
        torrent_list = torrent_handler.get_torrents()
        udp_torrents, http_torrnets = split_torrent_list(torrent_list)
        logging.debug(f"UDP TORRENTS LEN: {len(udp_torrents)}, TCP_TORRENTS_LEN: {len(http_torrnets)}")
        await asyncio.gather(udp_loop(udp_torrents, settings), http_loop(http_torrnets, settings))
        await asyncio.sleep(1)


async def announce_http_legacy(torrent: Torrent, event: str, settings: Settings):
    headers = {
        "Accept-Encoding": "gzip",
        "User-Agent": settings.peer_id,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # asyncio does not support passing both bytes and int, so decoding bytes
    #         "info_hash": base64.b64encode(torrent.info_hash).decode("ascii"),

    params = {
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
        params["event"] = ANNOUNCE_TABLE_HTTP[event]

    url = encode_params_with_url(params, torrent.connection_info.announce_url)
    async with aiohttp.ClientSession() as aiohttp_client:
        async with aiohttp_client.get(url=url, headers=headers) as resp:
            content = await resp.read()

    content = decode(content)[0]
    interval = content[b"interval"]
    peer_list = []

    peers = content[b"peers"]
    if peers and type(peers[0]) == dict:
        for peer_dict in peers:
            ip = peer_dict[b"ip"].split(b":")[-1].decode()
            if len(ip.split(".")) != 4:
                continue
            port = peer_dict[b"port"]
            peer_list.append((ip, port))
    else:
        peer_list_str = [peers[i:i + 6] for i in range(0, len(peers), 6)]
        for peer_data in peer_list_str:
            ip, port = struct.unpack('! 4s H', peer_data)
            ip = socket.inet_ntoa(ip)

            peer_list.append((ip, port))

    if b"incomplete" not in content:
        leechers = len(peer_list)
    else:
        leechers = content[b"incomplete"]

    if b"complete" not in content:
        seeders = 0
    else:
        seeders = content[b"complete"]

    torrent.peers = peer_list
    torrent.connection_info.time_to_announce = interval
    torrent.connection_info.leechers = leechers
    torrent.connection_info.seeders = seeders

    if event == announce_types.start:
        torrent.connection_info.state = torrent_types.started

    if event == announce_types.finish:
        torrent.connection_info.state = torrent_types.finished

    logging.info(f"updated torrent {torrent.name} connection info")


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
                       torrent.downloaded, torrent.size - torrent.downloaded, torrent.uploaded,
                       ANNOUNCE_TABLE_UDP[event], 0, key, -1, settings.port, 0)


def parse_announce_resp_struct(message):
    # 4 bytes action
    # 4 bytes trans_id
    # 4 bytes interval
    # 4 bytes leechers
    # 4 byte seeders
    tracker_data = message[:20]
    action, trans_id, interval, leechers, seeders = struct.unpack("! i 4s i i i", tracker_data)

    peers_data = message[20:]
    peers_data = [peers_data[i:i + 6] for i in range(0, len(peers_data), 6)]

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
    announce_data = announce_data.replace("udp://", "")
    announce_url, port = announce_data.split(":")
    port = int(port)
    addr = (announce_url, port)

    init_conn_msg = build_conn_struct(settings)
    resp, remote_conn = await init_conn(init_conn_msg, addr)
    conn_id, trans_id = vaildated_conn_id(resp)

    message = build_announce_struct(torrent, event, settings, conn_id, trans_id)
    remote_conn.send(message)
    response = await remote_conn.receive()

    remote_conn.close()
    # now we need to construct our announcing data
    interval, leechers, seeders, peer_list = parse_announce_resp_struct(response)

    torrent.peers = peer_list
    torrent.connection_info.time_to_announce = interval
    torrent.connection_info.leechers = leechers
    torrent.connection_info.seeders = seeders
    if event == announce_types.start:
        torrent.connection_info.state = torrent_types.started

    if event == announce_types.finish:
        torrent.connection_info.state = torrent_types.finished

    logging.info(f"updated torrent {torrent.name} connection info")

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
