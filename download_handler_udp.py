import struct
from torrent_handler import TorrentHandler
import asyncio
from torrent import Torrent
from piece_handler import PieceHandler
import aioudp
from settings.settings import Settings
from typing import List
import encryption
# import socket
import threading
import time

BLOCK_SIZE = 0x1000
MAX_TIME_TO_WAIT = 0.1
TYPES = {
    "REQUEST": 1,
    "PIECE": 2,
    "HASH": 3
}
# self_addr = (socket.gethostbyname(socket.getfqdn()) , settings.port)
self_addr = ("192.168.1.37", 25565)


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
    def __init__(self, peer_addr, conn, trans_id, peer_pub_key=None):
        self.peer_addr = peer_addr
        self.trans_id = trans_id
        self.conn_with_peer = conn
        self.peer_pub_key = peer_pub_key
        self.last_keep_alive = None
        print(f"{peer_addr} - {trans_id} - {peer_pub_key}")


async def connect_to_peer(peer_addr, public_key=None):
    ip, port = peer_addr.split(':')
    conn_with_peer = await aioudp.open_remote_endpoint(host=ip, port=port)
    msg = b'bittorrent'
    if public_key:
        msg += public_key
    conn_with_peer.send(msg)
    await conn_with_peer.drain()
    print("sent a connect msg to", peer_addr)
    try:
        resp = await asyncio.wait_for(conn_with_peer.receive(), timeout=1)
        if public_key:
            assert resp[1:] == public_key
        trans_id = resp[0]
        print("got a valid response")
        return connectableUDP((ip, port), conn_with_peer, trans_id, public_key)

    except TimeoutError:
        return None


class downloadHandlerUDP:
    """
    using bittorrentx protocol
    """

    def __init__(self, torrent: Torrent, settings: Settings) -> None:
        self.torrent = torrent
        self.settings = settings

        self.piece_handler = PieceHandler(self.torrent)

        self.block_offset = 0
        self.piece_index = self.piece_handler.needed_piece_to_download_index

        self.downloading = True if self.piece_index != -1 else False
        self.uploading = False if self.piece_index != -1 else True

        self.trans_id = 0
        self.peer_connections: List[connectableUDP] = []
        self.conn_as_server = None

        self.current_piece_data = bytearray([0]) * self.torrent.piece_size_in_bytes

        self.downloaded_piece = False
        self.validated_piece = False

        #self.self_addr = (socket.gethostbyname(socket.getfqdn()) , settings.port)
        self.self_addr = self_addr
        if settings.download_torrentx_encryption:
            self.pub_key, self.private_key = encryption.create_key_pairs()
        else:
            self.pub_key, self.private_key = None, None



    async def on_hash_request(self, msg, addr):
        length, msg_type, info_hash, piece_index, block_offset, block_length, _hash = struct.unpack("! i b 20s i i i 20s", msg)
        _hash = self.piece_handler.get_hash(piece_index, block_offset, block_length)

        hash_msg = struct.pack("! i b 20s i i i 20s", 20 + 20 + 4 + 4 + 4 + 1, 3, info_hash, piece_index, block_offset, length, _hash)

        self.conn_as_server.send(hash_msg, addr)
        await self.conn_as_server.drain()

    async def main_loop(self):
        self.conn_as_server = await aioudp.open_local_endpoint(*self.self_addr)
        print("started connection as server")
        while True:
            self.peer_connections += await self.gather_connectables()
            try:
                msg, addr = await asyncio.wait_for(self.conn_as_server.receive(), MAX_TIME_TO_WAIT)
            except TimeoutError:
                msg = None

            if msg:
                if b'bittorrent' == msg[:10]:
                    await self.on_peer_trying_to_connect(msg, addr)
                else:
                    # Everything done here is done as a connection of server
                    connectable = None
                    for conn in self.peer_connections:
                        if conn.peer_addr[0] == addr[0]:
                            connectable = conn
                            break

                    # then maybe its a message from peer with msg_type
                    try:
                        if msg[4] == 3:
                            await self.on_hash_request(msg, addr)
                        else:
                            print(msg[4])
                            msg_length, trans_id, msg_type, piece_index, block_offset, block_length = parse_request(msg)
                            if msg_type == 1:
                                await self.on_block_request(connectable, addr, trans_id, piece_index, block_offset,
                                                            block_length)
                            if msg_type == 2:
                                await self.on_block_receive(msg, piece_index, msg_length, block_offset, block_length)
                    except:
                        pass
            else:
                tasks = []
                for connection in self.peer_connections:
                    tasks.append(self.listen_for_msg(connection))

                await asyncio.gather(*tasks)

                if self.downloaded_piece and self.validated_piece:
                    self.current_piece_data = bytearray([0]) * self.torrent.piece_size_in_bytes
                    self.piece_index = self.piece_handler.needed_piece_to_download_index
                    self.block_offset = 0
                    self.downloaded_piece = False
                    self.validated_piece = False

                if self.piece_index == -1:
                    self.piece_handler.on_download_finish()

                if self.piece_handler.downloading:
                    print("gonna request block")
                    await self.request_block()

                await asyncio.sleep(MAX_TIME_TO_WAIT)


    async def gather_connectables(self):
        new_peers = []
        old_peer_ips = [peer.peer_addr[0] for peer in self.peer_connections]
        total_peers = self.torrent.peers
        new_peers = {peer for peer in total_peers if peer.split(":")[0] not in old_peer_ips}

        tasks = []
        for peer_addr in new_peers:
            if peer_addr.split(':')[0] == self.self_addr[0]:
                continue
            tasks.append(connect_to_peer(peer_addr, self.pub_key))

        res = await asyncio.gather(*tasks)
        return [item for item in res if item is not None]


    async def listen_for_msg(self, connectable: connectableUDP):
        try:
            data = await asyncio.wait_for(connectable.conn_with_peer.receive(), MAX_TIME_TO_WAIT)
            if type(connectable.conn_with_peer) == aioudp.RemoteEndpoint:
                msg = data
                addr = connectable.peer_addr
            else:
                msg = data[0]
                addr = data[1]

        except TimeoutError:
            msg = None

        if not msg:
            return None

        msg_length, trans_id, msg_type, piece_index, block_offset, block_length = parse_request(msg[:20])
        if msg_type == 1:
            await self.on_block_request(connectable, addr, trans_id, piece_index, block_offset, block_length)

        if msg_type == 2:
            await self.on_block_receive(msg, piece_index, msg_length, block_offset, block_length)

    async def on_peer_trying_to_connect(self, msg, addr):
        th = TorrentHandler("torrent.db")
        if (addr[0] == self.self_addr[0]):
            return
       
        trans_id = 1
        for torrent in th.get_torrents():
            addrs = [addr for addr, port in torrent.peers]
            if addr[0] in addrs:
                trans_id += 1

        resp = struct.pack('! b', trans_id)

        peer_pub_key = None
        if msg != b'bittorrent':  # then we also got a public key
            resp += msg[10:]
            peer_pub_key = msg[10:]

        self.conn_as_server.send(resp, addr)
        await self.conn_as_server.drain()
        connectable = connectableUDP(addr, self.conn_as_server, trans_id, peer_pub_key)
        self.peer_connections.append(connectable)

        print("handshake with ", addr, "complete")

    async def on_block_request(self, connectable, addr, trans_id, piece_index, block_offset, block_length):
        if connectable.peer_pub_key:
            data = self.piece_handler.return_block(piece_index, block_offset, encryption.MSG_SIZE_REQUEST_BYTES,
                                                   connectable.peer_pub_key)
        else:
            data = self.piece_handler.return_block(piece_index, block_offset, block_length, connectable.peer_pub_key)
        block_len = len(data)
        # print(f"data being sent: {data}")
        data = create_block_msg(data, trans_id, piece_index, block_offset, block_len)
        if type(connectable.conn_with_peer) == aioudp.RemoteEndpoint:
            connectable.conn_with_peer.send(data)
            await connectable.conn_with_peer.drain()
        else:
            connectable.conn_with_peer.send(data, addr)
            await connectable.conn_with_peer.drain()

        print(f"sent to peer data, piece index: {piece_index}, block offset: {block_offset}, block length: {block_len}")

    def on_piece(self, piece_index, offset):
        self.downloaded_piece = True
        print("not validated")
        if self.piece_handler.validate_piece(self.current_piece_data[:offset]):
            print("validated now")
            self.piece_handler.on_validated_piece(self.current_piece_data, piece_index)
            self.validated_piece = True

    async def on_block_receive(self, msg, piece_index, length, block_offset, block_length):
        print(f"got block: {block_offset}, got length: {block_length}, got block of piece: {piece_index}")
        data = msg[20: length + 1]

        if block_length == 0:
            return self.on_piece(piece_index, self.block_offset)

        if self.pub_key:
            data = encryption.decrypt_using_private(data, self.private_key)
            block_length = len(data)

        for i in range(block_length):
            if self.block_offset + i >= len(self.current_piece_data):
                # when we downloaded all piece
                print(f"downloaded all pieces")
                return self.on_piece(piece_index, self.block_offset + i)
            else:
                self.current_piece_data[i + self.block_offset] = data[i]

        self.block_offset += block_length
        print(f"progress in piece:", 100 * self.block_offset / (len(self.current_piece_data) + 1))

    async def request_block(self):
        # that function requests a block from all peers
            for connection in self.peer_connections:
                block_req_message = create_block_request_message(connection.trans_id, self.piece_index, self.block_offset,
                                                                 BLOCK_SIZE)

                if type(connection.conn_with_peer) == aioudp.RemoteEndpoint:
                    connection.conn_with_peer.send(block_req_message)
                    await connection.conn_with_peer.drain()

                else:
                    connection.conn_with_peer.send(block_req_message, connection.peer_addr)
                    await connection.conn_with_peer.drain()

async def main_loop(settings, torrent_handler):
    old_torrents = []
    while True:
        new_tasks = []
        for torrent in torrent_handler.get_torrents():
            if not torrent.is_torrentx:
                continue

            if torrent not in old_torrents:
                new_tasks.append(downloadHandlerUDP(torrent, settings).main_loop())
                old_torrents.append(torrent)
           
        threading.Thread(target=_run, args=(new_tasks, )).start()
        time.sleep(5)

def _run(tasks):
    asyncio.run(__run(tasks))

async def __run(tasks):
    await asyncio.gather(*tasks)
if __name__ == "__main__":
    from settings.settings import read_settings_file, Settings

    torrent_handler = TorrentHandler("torrent.db")
    from trakcer_announce_handler import main_loop as announce_main_loop

    settings = read_settings_file("./settings/settings.json")
    announce_handler = announce_main_loop(settings, torrent_handler)

    asyncio.run(announce_handler)

    torrent1 = torrent_handler.get_torrents()[0]
    asyncio.run(main_loop(settings, torrent_handler))
