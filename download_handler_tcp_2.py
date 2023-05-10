import struct
import sys
from typing import List

from connection_handlers import trakcer_announce_handler
from database.torrent_handler import TorrentHandler
from piece_handler import PieceHandler
from settings.settings import read_settings_file, Settings
from torrent import Torrent
import asyncio

from utils import msg_types

settings = read_settings_file("./settings/settings.json")
BLOCK_SIZE = 0x1000
MAX_TIME_TO_WAIT = 0.1

self_addr = ('192.168.1.41', settings.port)


class Handshake:
    identifer = "BitTorrent protocol".encode()
    identifier_length = 19
    total_payload_length = 68

    def __init__(self, info_hash: bytes, peer_id: bytes):
        self.peer_id = peer_id
        self.info_hash = info_hash

    def to_bytes(self):
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
        return self.bitfield[byte_index] >> (7 - offset) & 1 != 0

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
        return struct.pack('> i b i i i', total_length, msg_types.request, self.piece_index, self.begin,
                           self.piece_length)

    def cancel_to_bytes(self):
        total_length = 1 + 4 + 4 + 4
        return struct.pack('> i b i i i', total_length, msg_types.cancel, self.piece_index, self.begin,
                           self.piece_length)

    @classmethod
    def from_bytes(cls, payload):
        msg_length, msg_type, piece_index, piece_begin, piece_length = struct.unpack('> i b i i i', payload)

        if msg_type != msg_types.request:
            return None

        return Request(piece_index, piece_begin, piece_length)


class connectableTCP:
    def __init__(self, peer_addr, peer_reader, peer_writer):
        self.peer_addr = peer_addr
        self.peer_bitfield = None
        self.peer_choked = True
        self.interested = False
        self.choked = True
        self.peer_reader = peer_reader
        self.peer_writer = peer_writer


class downloadHandlerTCP:
    def __init__(self, torrent: Torrent, settings: Settings) -> None:
        self.pending = False
        self.torrent = torrent
        self.settings = settings
        self.piece_handler = PieceHandler(self.torrent)
        self.block_offset = 0
        self.current_piece_data = bytearray([0]) * self.torrent.pieces_info.piece_size_in_bytes

        self.self_addr = ('192.168.1.41', self.settings.port)

        self.peer_connections: List[connectableTCP] = []
        self.server = None
        self.current_peer = None
        self.loops_until_answer = 0

    async def make_handshake(self, peer_addr):
        try:
            peer_reader, peer_writer = await asyncio.wait_for(asyncio.open_connection(*peer_addr), 1)
        except TimeoutError:
            return None

        peer_writer.write(
            Handshake(self.torrent.info_hash, (self.settings.user_agent + self.settings.random_id).encode()).to_bytes())
        await peer_writer.drain()
        try:
            resp = await asyncio.wait_for(peer_reader.read(68), 1)
            if not Handshake.from_bytes(resp):
                return None
            print(f"CONNECTED {peer_addr}")
            return connectableTCP(peer_addr, peer_reader, peer_writer)


        except (TimeoutError, ConnectionResetError):
            peer_writer.close()
            await peer_writer.wait_closed()
            return None

    async def handle_client(self, reader, writer):
        # Read data from the client
        data = await reader.read(1024)
        message = data.decode()
        print(f'Received message: {message!r}')

        # Send a response back to the client
        response = f'Echoing message: {message}'
        writer.write(response.encode())
        await writer.drain()

        # Close the connection
        writer.close()

    async def main_loop(self):
        self.server = await asyncio.start_server(self.handle_client, *self.self_addr)
        print("started connection as server")
        self.peer_connections = await self.gather_connectables()
        self.current_peer = self.get_next_peer()
        while True:
            if self.loops_until_answer > 40:
                print("peer probably hanged on us, going to next peer and resetting stats")
                self.current_peer = self.get_next_peer()
                self.loops_until_answer = 0
                self.pending = False
            # tasks = []
            # for peer in self.peer_connections:
            #     tasks.append(self.handle_msg(peer))
            #
            # await asyncio.gather(*tasks)

            await self.handle_msg(self.current_peer)

            if self.piece_handler.needed_piece_to_download_index() != -1:
                self.loops_until_answer += 1
                if not self.pending:
                    await self.request_block(self.piece_handler.needed_piece_to_download_index(), self.block_offset)
                    self.pending = True
                    print(
                        f"PROGRESS IN PIECE: {round(100 * self.block_offset / self.torrent.pieces_info.piece_size_in_bytes, 2)}")
                    print(self.block_offset, self.torrent.pieces_info.piece_size_in_bytes)

            await asyncio.sleep(MAX_TIME_TO_WAIT)



    async def request_block(self, piece_index, block_offset):
        writer = self.current_peer.peer_writer
        request = Request(piece_index, block_offset, BLOCK_SIZE)
        writer.write(request.to_bytes())
        await writer.drain()

    async def handle_msg(self, peer: connectableTCP):
        reader, writer = peer.peer_reader, peer.peer_writer

        try:
            msg_len = await asyncio.wait_for(reader.read(4), MAX_TIME_TO_WAIT)
            msg_len = int.from_bytes(msg_len)

            payload = await asyncio.wait_for(reader.read(msg_len), MAX_TIME_TO_WAIT)
        except (TimeoutError, ConnectionAbortedError):
            return

        if payload == b"":
            # keep-alive
            return

        msg_id = payload[0]
        match msg_id:
            case msg_types.bitfield:
                peer.peer_bitfield = Bitfield.from_bytes(payload)

            case msg_types.unchoke:
                peer.choked = False

            # case msg_types.request:
            #     req = Request.from_bytes(payload)

            case msg_types.piece:
                self.on_block(msg_len, payload)

            case msg_types.choke:
                peer.peer_choked = True

        if not peer.interested:
            interested = struct.pack('> i b', 1, msg_types.interested)
            writer.write(interested)
            await writer.drain()
            peer.interested = True

        if peer.choked:
            unchoke = struct.pack('> i b', 1, msg_types.unchoke)
            writer.write(unchoke)
            await writer.drain()
            peer.choked = False

    async def gather_connectables(self):
        tasks = []
        for peer_addr in self.torrent.peers:
            if peer_addr[0] in [peer.peer_addr[0] for peer in self.peer_connections]:
                continue

            tasks.append(self.make_handshake(peer_addr))
        res = await asyncio.gather(*tasks)
        to_ret = [item for item in res if item is not None]

        import random
        random.shuffle(to_ret)
        return to_ret

    def on_block(self, msg_len, payload):
        msg_type, piece_index, block_offset = struct.unpack('! b i i', payload[:9])
        block_length = msg_len - 9
        block = payload[9:]

        print(
            f"piece index {piece_index}    block offset {block_offset}    block length recv {block_length}    block actual length {len(block)}")

        is_piece_success = self.write_data_to_block(piece_index, block_offset, block_length, block)

        if is_piece_success:
            print("Success on getting piece! Yay")
            self.block_offset = 0

        if is_piece_success is None:
            self.block_offset = block_offset + block_length
        elif not is_piece_success:
            print("Didn't get piece. trying again")
            self.block_offset = 0

        self.loops_until_answer = 0
        self.pending = False

    def get_next_peer(self):
        return self.peer_connections.pop()

    def write_data_to_block(self, piece_index, block_offset, block_length, block):
        if piece_index != self.piece_handler.needed_piece_to_download_index():
            # something went wrong in reading that message so we want it all over again
            return False

        for i in range(block_length):
            if block_offset + i >= len(self.current_piece_data):
                # when we downloaded all piece
                print(f"think we downloaded")
                with open("current_piece", 'wb') as f:
                    f.write(self.current_piece_data)
                if self.piece_handler.validate_piece(self.current_piece_data):
                    print("piece hash validated")
                    return True
                else:
                    return False

            else:
                if i < len(block):
                    self.current_piece_data[i + self.block_offset] = block[i]
                else:
                    self.current_piece_data[i + self.block_offset] = 0

        if self.block_offset + block_length == self.torrent.pieces_info.piece_size_in_bytes:
            print(f"think we downloaded")
            with open("current_piece", 'wb') as f:
                f.write(self.current_piece_data)
            if self.piece_handler.validate_piece(self.current_piece_data):
                self.piece_handler.on_validated_piece(self.current_piece_data,
                                                      self.piece_handler.needed_piece_to_download_index())
                return True

            else:
                print("piece not validated")
                return False

        return None


torrent_handler = TorrentHandler("./database/torrent.db")

torrent1 = None
for torrent in torrent_handler.get_torrents():
    if not torrent.is_torrentx:
        torrent1 = torrent
        break
#
tcp = downloadHandlerTCP(torrent1, settings)
asyncio.run(trakcer_announce_handler.main_loop(settings, torrent_handler))
asyncio.run(tcp.main_loop())
