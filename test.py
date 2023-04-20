import struct

from connection_handlers.new_PeerHandler import ConnectedPeer, make_handshake, Request
from connection_handlers import trakcer_request_handler

from database.torrent_handler import TorrentHandler
from settings.settings import read_settings_file
import asyncio
import threading

BLOCK_LENGTH = 0x10000


class downloadHandler:
    def __init__(self, torrent, settings) -> None:
        self.torrent = torrent
        self.settings = settings
        self.connections = []

        self.piece_list_length = len(self.torrent.pieces_info.pieces_hashes_list)
        self.current_piece_index = 0
        self.current_block_index = 0
        self.current_piece_data = bytearray([0]) * self.torrent.pieces_info.piece_size_in_bytes

    def gatherConnectables(self):
        connectables = [make_handshake(torrent1, settings, peer) for peer in torrent1.peers]
        connectables = [x for x in connectables if x is not None]
        self.connections = [ConnectedPeer(self.torrent, self.settings, x, self) for x in connectables]

    def startConnectables(self):
        # start the socket with peer
        for connectable in self.connections:
            threading.Thread(target=connectable.run).start()
        print("started connection thread")

    def request_block(self):
        request = Request(self.current_piece_index, self.current_block_index, BLOCK_LENGTH)
        for connection in self.connections:
            connection.set_request_message(request.to_bytes())

    def cancel_block(self):
        request = Request(self.current_piece_index, self.current_block_index, BLOCK_LENGTH)
        for connection in self.connections:
            connection.set_request_message(request.cancel_to_bytes())

    def get_block_in_piece(self, payload):
        # will put the data from a block in piece
        self.cancel_block()

        block = payload[9:]

        # self.save_block_to_piece(block)
        self.get_next_block()

    def validate_piece(self):
        pass

    def save_block_to_piece(self, block):

        for i in range(min(len(block), self.torrent.pieces_info.piece_size_in_bytes)):
            self.current_piece_data[self.current_block_index + i] = block[i]

        print("saved block to piece.")

    def get_next_block(self):
        print("piece size: ", self.torrent.pieces_info.piece_size_in_bytes)
        print("current block offset: ", self.current_block_index)
        # we dont have the risk of asking for a block longer then piece size because it will just be padded with 0
        if self.current_block_index >= self.torrent.pieces_info.piece_size_in_bytes:
            self.current_piece_index += 1
            self.current_block_index = 0
        else:
            self.current_block_index += BLOCK_LENGTH

        if self.current_piece_index > self.piece_list_length:
            print("download finished")
        else:
            print(f"getting {self.current_piece_index} from {self.piece_list_length}")
            self.request_block()


torrent_handler = TorrentHandler("./database/torrent.db")
settings = read_settings_file("./settings/settings.json")

torrent1 = torrent_handler.get_torrents()[1]

asyncio.run(trakcer_request_handler.main_loop(settings, torrent_handler))
x = downloadHandler(torrent1, settings)
x.gatherConnectables()
x.startConnectables()
x.request_block()
