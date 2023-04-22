import struct

from connection_handlers.peer_handler import ConnectedPeer, make_handshake, Request
from connection_handlers import trakcer_announce_handler

from database.torrent_handler import TorrentHandler
from settings.settings import read_settings_file
import asyncio
import threading
from torrent import Torrent
from piece_handler import PieceHandler

BLOCK_SIZE = 0x100


class downloadHandlerTCP:
    def __init__(self, torrent, settings):
        self.torrent = torrent
        self.settings = settings
        self.connections = []
        self.current_piece_data = bytearray([0]) * self.torrent.pieces_info.piece_size_in_bytes
        self.ph = PieceHandler(torrent)

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
            if i < len(block):
                self.current_piece_data[i + block_offset] = block[i]
            else:
                self.current_piece_data[i + block_offset] = 0

        next_offset = block_offset + block_length
        if block_offset + block_length >= self.torrent.pieces_info.piece_size_in_bytes:
            self.ph.on_validated_piece(self.current_piece_data)
            next_offset = 0
        self.download_block(self.ph.needed_piece_to_download_index(), next_offset, BLOCK_SIZE)

    def gatherConnectables(self):
        import random
        random.shuffle(torrent1.peers)
        for peer in torrent1.peers:
            res = make_handshake(torrent1, settings, peer)
            if res:
                self.connections = [ConnectedPeer(res, self)]
                break

    def startConnectables(self):
        for connectable in self.connections:
            threading.Thread(target=connectable.run).start()
        print("connected to each peer that we had a handshake with")


torrent_handler = TorrentHandler("./database/torrent.db")
settings = read_settings_file("./settings/settings.json")

torrent1 = torrent_handler.get_torrents()[0]
# asyncio.run(trakcer_announce_handler.main_loop(settings, torrent_handler))

# x = downloadHandlerTCP(torrent1, settings)
# x.gatherConnectables()
# x.startConnectables()
# x.run()

import aioudp
from typing import List

TYPES = {
    "REQUEST": 1,
    "PIECE": 2,
    "NO PIECE": 3,
    "KEEP ALIVE": 4
}


def parse_request(payload):
    return struct.unpack('i b b i i i', payload)

def create_block_msg(data, trans_id, piece_index, block_offset, block_length):
    # 4 bytes - length
    # 1 bytes - trans id
    # 1 bytes - msg type
    # 4 bytes - piece
    # 4 bytes - block offset
    # 4 bytes - block length
    # rest - data
    return struct.pack('i b b i i i', 4 + 1 + 1 + 4 + 4 + 4 + len(data) + 1, trans_id, TYPES["PIECE"], piece_index,
                       block_offset, block_length) + data


def create_block_request_message(trans_id, piece_index, block_offset, block_length):
    # 4 bytes - length
    # 1 bytes - trans id
    # 1 bytes - msg type
    # 4 bytes - piece
    # 4 bytes - block offset
    # 4 bytes - block length

    return struct.pack('i b b i i i', 4 + 1 + 1 + 4 + 4 + 4, trans_id, TYPES['REQUEST'], piece_index, block_offset,
                       block_length)


class connectableUDP:
    def __init__(self, peer_addr, conn, trans_id):
        self.peer_addr = peer_addr
        self.trans_id = trans_id
        self.conn_with_peer = conn
        print(f"{peer_addr} - {trans_id}")


async def connect_to_peer(peer_addr):
    conn_with_peer = await aioudp.open_remote_endpoint(peer_addr)
    conn_with_peer.send(b'bittorrent')
    try:
        trans_id = await asyncio.wait_for(conn_with_peer.receive(), timeout=1)
        return connectableUDP(peer_addr, conn_with_peer, trans_id)

    except TimeoutError:
        return None


MAX_TIME_TO_WAIT = 0.1


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
        self.uploading = False if self.piece_index != -1 else True

        self.trans_id = 0
        self.peer_connections: List[connectableUDP] = []
        self.conn_as_server = None


        self.current_piece_data = bytearray([0]) * self.torrent.pieces_info.piece_size_in_bytes

    async def main_loop(self):
        self.conn_as_server = await aioudp.open_local_endpoint("127.0.0.1", 1234)
        print("started connection as server")
        await self.gather_connectables()
        print("gathered all peers")

        while True:
            try:
                msg, addr = await asyncio.wait_for(self.conn_as_server.receive(), MAX_TIME_TO_WAIT)
            except TimeoutError:
                msg = None

            if msg == b'bittorrent':
                print("got a new connection")
                await self.on_peer_trying_to_connect(addr)
                print("added incoming connection to my connections")

            tasks = []
            for connection in self.peer_connections:
                tasks.append(self.listen_for_msg(connection))

            await asyncio.gather(*tasks)
            print("finished listening for requests from peers")
            # after we finished with requests we need to make sure that we didnt get any new requests

            print("now requesting from peers")
            self.request_block()
            await asyncio.sleep(MAX_TIME_TO_WAIT)

    async def gather_connectables(self):
        for peer_addr in self.torrent.peers:
            res = await connect_to_peer(peer_addr)
            if res:
                self.peer_connections.append(res)

    async def listen_for_msg(self, connectable: connectableUDP):
        try:
            msg, addr = await asyncio.wait_for(connectable.conn_with_peer.receive(), MAX_TIME_TO_WAIT)

        except TimeoutError:
            msg = None

        if not msg:
            return None

        msg_length, trans_id, msg_type, piece_index, block_offset, block_length = parse_request(msg)
        if msg_type == 1:
            await self.on_block_request(connectable, addr, trans_id, piece_index, block_offset, block_length)

        if msg_type == 2:
            await self.on_block_receive(msg, msg_length, block_offset, block_length)

        if msg_type == 3:
            # block does not exist, for now in current implementation we just pass
            pass

    async def on_peer_trying_to_connect(self, addr):
        th = TorrentHandler("./database/torrent.db")
        trans_id = 1
        for torrent in th.get_torrents():
            addrs = [addr for addr, port in torrent.peers]
            if addr[0] in addrs:
                trans_id += 1

        print("decided trans id:", trans_id)
        self.conn_as_server.send(struct.pack('b', trans_id), addr)
        connectable = connectableUDP(addr, self.conn_as_server, trans_id)
        self.peer_connections.append(connectable)

    async def on_block_request(self, connectable, addr, trans_id, piece_index, block_offset, block_length):
        data = self.piece_handler.return_block(piece_index, block_offset, block_length)
        block_len = len(data)
        print(f"data being sent: {data}")
        data = create_block_msg(data, trans_id, piece_index, block_offset, block_len)
        connectable.conn_with_peer.send(data, addr)
        print(f"sent to peer data, piece index: {piece_index}, block offset: {block_offset}, block length: {block_len}")

    async def on_block_receive(self, msg, length, block_offset, block_length):
        data = msg[20: length + 1]
        print(f"block is: {data}")
        for i in range(block_length):
            self.current_piece_data[i + block_offset] = data[i]

        if block_offset + 1 >= len(self.current_piece_data):
            self.piece_handler.on_validated_piece(self.current_piece_data)
            self.piece_index = self.piece_handler.needed_piece_to_download_index()
            self.block_offset = 0

        else:
            self.block_offset += block_length

    def request_block(self):
        # that function requests a block from all peers
        for connection in self.peer_connections:
            block_req_message = create_block_request_message(connection.trans_id, self.piece_index, self.block_offset, BLOCK_SIZE)
            connection.conn_with_peer.send(block_req_message)
            

udp = downloadHandlerUDP(torrent1)
asyncio.run(trakcer_announce_handler.main_loop(settings, torrent_handler))
asyncio.run(udp.main_loop())
