import struct
from connection_handlers.peer_handler import ConnectedPeer, make_handshake, Request
from database.torrent_handler import TorrentHandler
from connection_handlers.trakcer_announce_handler import main_loop
from settings.settings import read_settings_file
import threading
from piece_handler import PieceHandler

BLOCK_SIZE = 0x1000


class downloadHandlerTCP:
    def __init__(self, torrent, settings):
        self.torrent = torrent
        self.settings = settings
        self.connections = []
        self.current_piece_data = bytearray([0]) * self.torrent.pieces_info.piece_size_in_bytes
        self.ph = PieceHandler(torrent)

    # def download_piece(self, needed_piece_index):
    #     connected_peers = len(self.connections)
    #     piece_size = len(self.current_piece_data)
    #
    #     to_download_block_size = piece_size // connected_peers
    #     last_block_modolu = piece_size % connected_peers # download the sheerit from the last connected
    #
    #     offset = 0
    #
    #     for connection in self.connections:
    #         request = Request(needed_piece_index, offset, to_download_block_size)
    #         connection.to_send.append(request.to_bytes())
    #         offset += to_download_block_size
    #     pass

    def download_block(self, needed_piece, block_offset, block_size):
        request = Request(needed_piece, block_offset, block_size)
        for connection in self.connections:
            connection.to_send.append(request.to_bytes())

    def run(self):
        # thats how we gather blocks
        needed_piece = self.ph.needed_piece_to_download_index()
        block_offset = 0
        self.download_block(needed_piece, block_offset, BLOCK_SIZE)

    def on_block(self, msg_len, payload):
        msg_type, piece_index, block_offset = struct.unpack('! b i i', payload[:9])
        block_length = msg_len - 9
        block = payload[9:]

        for i in range(block_length):
            try:
                if i < len(block):
                    self.current_piece_data[i + block_offset] = block[i]
                else:
                    self.current_piece_data[i + block_offset] = 0
            except Exception as e:
                break

        next_offset = block_offset + block_length
        if next_offset >= self.torrent.pieces_info.piece_size_in_bytes:
            print("got whole piece")
            self.ph.on_validated_piece(self.current_piece_data, piece_index)
            next_offset = 0
        else:
            print("progress on piece:", block_offset /self.torrent.pieces_info.piece_size_in_bytes * 100)
        self.download_block(self.ph.needed_piece_to_download_index(), next_offset, BLOCK_SIZE)

    def gatherConnectables(self):
        import random
        random.shuffle(torrent1.peers)
        for peer in torrent1.peers:
            res = make_handshake(torrent1, settings, peer)
            if res:
                self.connections.append(ConnectedPeer(res, self))

    def startConnectables(self):
        for connectable in self.connections:
            threading.Thread(target=connectable.run).start()
        print("connected to each peer that we had a handshake with")


torrent_handler = TorrentHandler("./database/torrent.db")
settings = read_settings_file("./settings/settings.json")

torrent1 = None
for torrent in torrent_handler.get_torrents():
    if not torrent.is_torrentx:
        torrent1 = torrent
        break

import asyncio

asyncio.run(main_loop(settings, torrent_handler))

x = downloadHandlerTCP(torrent1, settings)
x.gatherConnectables()
x.startConnectables()
x.run()
