import struct
import socket
from torrent import Torrent
from settings.settings import Settings
from utils import msg_types
import time
import random


class Handshake:
    identifer = "BitTorrent protocol".encode()
    identifier_length = 19
    total_payload_length = 68

    def __init__(self, info_hash: bytes, peer_id: bytes):
        self.peer_id = peer_id
        self.info_hash = info_hash

    def into_bytes(self):
        return struct.pack("> b 19s q 20s 20s", self.identifier_length, self.identifer, 0, self.info_hash, self.peer_id)

    @classmethod
    def from_bytes(cls, payload):
        try:
            identifer_length, _, _, info_hash, peer_id = struct.unpack("> b 19s q 20s 20s", payload[:68])
        except struct.error:
            return None

        if identifer_length != 19:
            return None

        return Handshake(info_hash, peer_id)
    


class Bitfield:
    def __init__(self, bitfield: bytes):
        self.bitfield = bitfield


    def to_bytes(self):
        return struct.pack(f'> i b {len(self.bitfield)}s', 1 + len(self.bitfield), msg_types.bitfield, self.bitfield)

    def has_piece(self, piece_index):
        byte_index = piece_index / 8
        offset = piece_index % 8
        return self.bitfield[byte_index] >> (7-offset)&1 != 0
    

    @classmethod
    def from_bytes(cls, payload):
        try:
            msg_id, bitfield = struct.unpack(f'> b {len(payload) - 1}s', payload)
        except struct.error:
            return None
        if msg_types.bitfield != msg_id:
            return None

        return Bitfield(bitfield)


class Request:
    def __init__(self, piece_index, begin, piece_length):
        self.begin = begin
        self.piece_index = piece_index
        self.piece_length = piece_length

    def to_bytes(self):
        total_length = 1 + 4 + 4 + 4
        return struct.pack('> i b i i i', total_length, msg_types.request, self.piece_index, self.begin, self.piece_length)


    @classmethod
    def from_bytes(cls, payload):
        msg_length, msg_type, piece_index, piece_begin, piece_length = struct.unpack('> i b i i i', payload)

        if msg_type != msg_types.request:
            return None


        return Request(piece_index, piece_begin, piece_length)

def make_handshake(torrent: Torrent, settings: Settings, peer_addr):
    handshake = Handshake(torrent.info_hash, (settings.user_agent + settings.random_id).encode())


    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.1)
    try:
        sock.connect(peer_addr)
        sock.send(handshake.into_bytes())
        data = sock.recv(68)

    except (TimeoutError, ConnectionResetError):
        print("unconnectable")
        sock.close()
        return None

    if not Handshake.from_bytes(data):
        print("unconnectable")
        sock.close()
        return None

    else:
        print("connectable", peer_addr)
        return sock


class ConnectedPeer:
    def __init__(self, torrent: Torrent, settings: Settings, sock: socket.socket):
        self.torrent = torrent
        self.settings = settings
        self.sock = sock

        self.peer_bitfield = None
        self.peer_choked = True
        self.choked = True
        self.interested = False

    def run(self):
        try:
            self.sock.settimeout(None)
            # first we will init our bitfield

            my_bitfield = Bitfield(bytes([0]) * len(self.torrent.pieces_info.pieces_hashes))
            # self.sock.send(my_bitfield.to_bytes())
            # print("sent bitfield to peer")

            while True:
                msg_len = self.sock.recv(4)
                msg_len = int.from_bytes(msg_len)

                payload = self.sock.recv(msg_len)

                if payload == b"":
                    # keep-alive
                    continue

                msg_id = payload[0]
                print("got from peer msg:", msg_id)

                match msg_id:
                    case msg_types.bitfield:
                        print("got bitfield from peer")
                        self.peer_bitfield = Bitfield.from_bytes(payload)

                    case msg_types.unchoke:
                        print("got unchoke from peer")
                        self.choked = False
                        self.peer_choked = False

                    case msg_types.request:
                        print("got request from peer")
                        req = Request.from_bytes(payload)

                    case msg_types.piece:
                        print("got piece")
                        exit(1)

                    case msg_types.choke:
                        print("peer choked us")
                        self.peer_choked = True

                if not self.interested:
                    interested = struct.pack('> i b', 1, msg_types.interested)
                    self.sock.send(interested)
                    self.interested = True
                    print("sent interested to peer")

                if self.choked:
                    unchoke = struct.pack('> i b', 1, msg_types.unchoke)
                    # self.sock.send(unchoke)
                    self.choked = False
                    print("sent to peer that he is unchoked to me")


                req = Request(140, 1, 0x0400)
                self.sock.send(req.to_bytes())
                print("told peer im interested in piece")

                time.sleep(5)
        except Exception as e:
            print(e.__str__())


