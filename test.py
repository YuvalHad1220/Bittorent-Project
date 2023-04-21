import struct

from connection_handlers.peer_handler import ConnectedPeer, make_handshake, Request
from connection_handlers import trakcer_announce_handler

from database.torrent_handler import TorrentHandler
from settings.settings import read_settings_file
import asyncio
import threading

BLOCK_SIZE = 0xf00


class downloadHandler:
    def __init__(self, torrent, settings):
        self.torrent = torrent
        self.settings = settings
        self.connections = []

        self.piece_list_length = len(self.torrent.pieces_info.pieces_hashes_list)
        self.piece_size = self.torrent.pieces_info.piece_size_in_bytes
        self.current_piece_index = 0
        self.current_piece_data = bytearray([0]) * self.torrent.pieces_info.piece_size_in_bytes
        self.block_offset = 0
        self.req = None

    def gatherConnectables(self):
        connectables = [make_handshake(torrent1, settings, peer) for peer in torrent1.peers]
        connectables = [connectable for connectable in connectables if connectable is not None]
        self.connections = [ConnectedPeer(x, self) for x in connectables]

    def startConnectables(self):
        for connectable in self.connections:
            threading.Thread(target=connectable.run).start()
        print("connected to each peer that we had a handshake with")

    def request_block(self):
        self.req = Request(self.current_piece_index, self.block_offset, BLOCK_SIZE)
        for connection in self.connections:
            connection.to_send.append(self.req.to_bytes())

    def on_block(self, payload):
        block = payload[9:]

        self.save_block_to_piece(block)
        self.get_next_block(block)

    def validate_piece(self):
        pass

    def save_block_to_piece(self, block):
        # for i in range(len(block)):
        #     self.current_piece_data[self.block_offset + i] = block[i]
        pass
    def get_next_block(self, block):
        if self.current_piece_index > self.piece_list_length:
            print("finished downloading!!!!")
            exit(-1)
        if len(block) + self.block_offset >= self.piece_size:
            self.block_offset = 0
            self.current_piece_index += 1
        else:
            self.block_offset += len(block)

        print(round(100 * self.block_offset / self.piece_size,2), "% in piece")
        print(round(100 * self.current_piece_index / self.piece_list_length), "% in torrent")
        self.request_block()


torrent_handler = TorrentHandler("./database/torrent.db")
settings = read_settings_file("./settings/settings.json")

torrent1 = torrent_handler.get_torrents()[0]

asyncio.run(trakcer_request_handler.main_loop(settings, torrent_handler))
x = downloadHandler(torrent1, settings)
x.gatherConnectables()
x.startConnectables()
x.request_block()
