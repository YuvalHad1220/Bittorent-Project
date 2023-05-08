import struct

from connection_handlers import trakcer_announce_handler
from database.torrent_handler import TorrentHandler
import asyncio
from torrent import Torrent
from piece_handler import PieceHandler
import aioudp
from settings.settings import read_settings_file, Settings
from typing import List
import encryption

BLOCK_SIZE = 0x100
MAX_TIME_TO_WAIT = 0.1
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
    def __init__(self, peer_addr, conn, trans_id, peer_pub_key = None):
        self.peer_addr = peer_addr
        self.trans_id = trans_id
        self.conn_with_peer = conn
        self.peer_pub_key = peer_pub_key
        print(f"{peer_addr} - {trans_id}")


async def connect_to_peer(peer_addr, public_key = None):
    conn_with_peer = await aioudp.open_remote_endpoint(peer_addr)
    msg = b'bittorrent'
    if public_key:
        msg += public_key
    conn_with_peer.send(msg)
    try:
        resp = await asyncio.wait_for(conn_with_peer.receive(), timeout=1)
        if public_key:
            assert resp[1:] == public_key
        trans_id = resp[0]
        return connectableUDP(peer_addr, conn_with_peer, trans_id)

    except TimeoutError:
        return None



class downloadHandlerUDP:
    """
    using bittorrentx protocol
    """

    def __init__(self, torrent: Torrent, settings: Settings) -> None:
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

        if settings.download_torrentx_encryption:
            self.pub_key, self.private_key = encryption.create_key_pairs()
        else:
            self.pub_key, self.private_key = None, None


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

            if b'bittorrent' in msg:
                print("got a new connection")
                await self.on_peer_trying_to_connect(msg, addr)
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
            res = await connect_to_peer(peer_addr, self.pub_key)
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

    async def on_peer_trying_to_connect(self, msg, addr):
        th = TorrentHandler("./database/torrent.db")
        trans_id = 1
        for torrent in th.get_torrents():
            addrs = [addr for addr, port in torrent.peers]
            if addr[0] in addrs:
                trans_id += 1

        print("decided trans id:", trans_id)

        resp = struct.pack('! b', trans_id)

        peer_pub_key = None
        if msg != b'bittorrent': # then we also got a public key
            resp += msg[10:]
            peer_pub_key = msg[10:]
        self.conn_as_server.send(resp, addr)
        connectable = connectableUDP(addr, self.conn_as_server, trans_id, peer_pub_key)
        self.peer_connections.append(connectable)

    async def on_block_request(self, connectable, addr, trans_id, piece_index, block_offset, block_length):
        data = self.piece_handler.return_block(piece_index, block_offset, block_length, connectable.peer_pub_key)
        block_len = len(data)
        print(f"data being sent: {data}")
        data = create_block_msg(data, trans_id, piece_index, block_offset, block_len)
        connectable.conn_with_peer.send(data, addr)
        print(f"sent to peer data, piece index: {piece_index}, block offset: {block_offset}, block length: {block_len}")

    async def on_block_receive(self, msg, length, block_offset, block_length):
        data = msg[20: length + 1]
        if self.pub_key:
            data = encryption.decrypt_using_private(data, self.private_key)
            block_length = len(data)

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
            


torrent_handler = TorrentHandler("./database/torrent.db")
settings = read_settings_file("./settings/settings.json")

torrent1 = None
for torrent in torrent_handler.get_torrents():
    if torrent.is_torrentx:
        torrent1 = torrent
        break

udp = downloadHandlerUDP(torrent1, settings)
asyncio.run(trakcer_announce_handler.main_loop(settings, torrent_handler))
asyncio.run(udp.main_loop())