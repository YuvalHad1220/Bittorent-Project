"""
Main part where we will request pieces, write them etc
"""

from torrent import Torrent
from settings.settings import Settings
import struct
import socket
import time

def get_piece(torrent: Torrent, piece_index, peers_list, settings: Settings):
    # building a request message, than sending it to all peers. once we got one valid we drop all connections
    peer_id = settings.user_agent + settings.random_id
    peer_id = peer_id.encode()
    reserved = b'\x00\x00\x00\x00\x00\x00\x00\x00' # reserved bytes

    packed = struct.pack(">b 19s 8s 20s 20s", 19, b"BitTorrent protocol", reserved, torrent.info_hash, peer_id)
    print(packed)
    print(len(packed))
    cntr = 0

    for peer in peers_list:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect(peer)
            client_socket.send(packed)
            resp = client_socket.recv(68)

            cntr = 0
            while resp == b'' and cntr < 20:
                print("got empty")
                resp = client_socket.recv(68)
                cntr += 1
                time.sleep(1)
            print(resp)

        except:
            print("failed peer:", peer)
            continue

    exit(-1)
