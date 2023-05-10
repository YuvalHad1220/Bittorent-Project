import struct
import sys

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


        print(f"piece index {piece_index}    block offset {block_offset}    block length recv {block_length}    block actual length {len(block)}")

        self.download_block(self.ph.needed_piece_to_download_index(), block_offset + block_length, BLOCK_SIZE)

        #
        # for i in range(block_length):
        #     try:
        #         if i < len(block):
        #             self.current_piece_data[i + block_offset] = block[i]
        #         else:
        #             self.current_piece_data[i + block_offset] = 0
        #     except Exception as e:
        #         break
        #
        # next_offset = block_offset + block_length
        # if next_offset >= self.torrent.pieces_info.piece_size_in_bytes:
        #     print("got whole piece")
        #     self.ph.on_validated_piece(self.current_piece_data, piece_index)
        #     next_offset = 0
        # else:
        #     print("progress on piece:", block_offset /self.torrent.pieces_info.piece_size_in_bytes * 100)

        # if block_length == 0:
        #     return self.on_piece(piece_index, self.block_offset)
        #
        # for i in range(block_length):
        #     if block_offset + i >= len(self.current_piece_data):
        #         # when we downloaded all piece
        #         print(f"think we downloaded")
        #         return self.on_piece(piece_index, block_offset + i)
        #     else:
        #         try:
        #             self.current_piece_data[i + block_offset] = block[i]
        #         except Exception as e:
        #             pass
        # print(f"got from peer data", 100 * block_offset / (len(self.current_piece_data) + 1))
        #
        # self.on_piece(piece_index, block_offset + block_length)

    def on_piece(self, piece_index, offset):
        print("not validated")
        if self.ph.validate_piece(self.current_piece_data[:offset]):
            print("validated now")
            self.ph.on_validated_piece(self.current_piece_data, piece_index)

    def gatherConnectables(self):
        for peer in torrent1.peers:
            res = make_handshake(torrent1, settings, peer)
            if res:
                self.connections.append(ConnectedPeer(res, self))

    def start_new_conn(self):
        conn = self.connections.pop()
        threading.Thread(target=conn.run).start()
        print("started connection with new peer")


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
x.start_new_conn()
x.run()
