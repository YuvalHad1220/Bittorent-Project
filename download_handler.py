import struct

from connection_handlers.peer_handler import ConnectedPeer, make_handshake, Request
from connection_handlers import trakcer_announce_handler

from database.torrent_handler import TorrentHandler
from settings.settings import read_settings_file
import asyncio
import threading
from torrent import Torrent
from piece_handler import PieceHandler
BLOCK_SIZE = 0x1000


class downloadHandlerTCP:
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

    def on_block(self, msg_len, payload):
        # <offset> is a 4-byte integer indicating the offset of this block within the piece, in bytes.

        msg_type, piece_index, block_offset = struct.unpack('! b i i', payload[:9])
        block = payload[9:]

        self.build_piece_into_file_and_update(block, block_offset, msg_len)
        self.request_block()


    def build_piece_into_file_and_update(self, data, offset, msg_length):
        block_length = msg_length - 9 # first 4 bytes is the original length of the message, 9 bytes is for other unrelated data
        # print(f"recieved block length: {block_length} actual block_length: {len(data)} requested block length {BLOCK_SIZE}")
        print(data)
        for i in range(len(data)):
            self.current_piece_data[i + offset] = data[i]


        self.block_offset += block_length

        if self.block_offset + 1 >= self.piece_size:
            print(self.current_piece_data)

            self.current_piece_index += 1
            self.block_offset = 0
            print("moving into next piece")

        else:
            print(f"offset: {self.block_offset} piece_size: {self.piece_size}")
    



torrent_handler = TorrentHandler("./database/torrent.db")
settings = read_settings_file("./settings/settings.json")

torrent1 = torrent_handler.get_torrents()[0]
asyncio.run(trakcer_announce_handler.main_loop(settings, torrent_handler))

x = downloadHandlerTCP(torrent1, settings)
x.gatherConnectables()
x.startConnectables()
x.request_block()


import aioudp
from typing import List
TYPES = {
    "REQUEST": 1,
    "PIECE": 2,
    "NO PIECE": 3,
    "KEEP ALIVE": 4
}


class connectableUDP:
    def __init__(self, peer_addr, conn, trans_id):
        self.peer_addr = peer_addr
        self.trans_id = trans_id
        self.conn_with_peer = conn


async def connectToPeerUDP(peer_addr):
    conn_with_peer = await aioudp.open_remote_endpoint(peer_addr)
    conn_with_peer.send(b'bittorrent')
    try:
        trans_id = await asyncio.wait_for(conn_with_peer.receive(), timeout=1)
        return connectableUDP(peer_addr, conn_with_peer, trans_id)
    
    except TimeoutError:
        return None


class downloadHandlerUDP:
    """
    using bittorrentx protocol
    """

    def __init__(self, torrent: Torrent) -> None:
        self.torrent = torrent

        self.piece_handler = PieceHandler(self.torrent)

        self.block_offset = 0
        self.piece_index = self.piece_handler.needed_piece_to_download_index()

        self.downloading = True if self.piece_index != -1 else False
        self.uploading = True

        self.trans_id = 0
        self.peer_connections = List[connectableUDP]
        self.my_connection = None


    async def main_loop(self):
        conn_as_server = await aioudp.open_local_endpoint("127.0.0.1", 1234)
        while True:
            tasks = []
            for connection in self.peer_connections:
                tasks.append(self.listen_for_msg(connection))

            await asyncio.gather(*tasks)

            # after we finished with requests we need to make sure that we didnt get any new requests

            msg, addr = await asyncio.wait_for(conn_as_server.receive(), 1)

            if msg == b'bittorrent':
                self.onPeerTryingToConnectUDP(addr)

            # after we added that connection to conns we have then we are fine
    async def gather_connectables(self):
        for peer_addr in self.torrent.peers:
            res = await connectToPeerUDP(peer_addr)
            if res:
                self.peer_connections.append(res)

    async def listen_for_msg(self, connectable: connectableUDP):
        msg, addr = await asyncio.wait_for(connectable.conn_with_peer.recieve(), 1)
        if msg:
            # do something with msg
            pass


    async def onPeerTryingToConnectUDP(self, addr):
        trans_id = TorrentHandler("...").get_by_addr(addr)
        pass

    async def on_piece_request(self):
        pass

    async def on_piece_recieve(self):
        pass




