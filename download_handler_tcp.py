import struct
from typing import List

import trakcer_announce_handler
from database.torrent_handler import TorrentHandler
from piece_handler import PieceHandler
from settings.settings import read_settings_file, Settings
from torrent import Torrent
import asyncio
import socket


from utils import msg_types, Request, Bitfield, Handshake

BLOCK_SIZE = 0x1000
MAX_TIME_TO_WAIT = 0.1

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
        self.current_piece_data = bytearray([0]) * self.torrent.piece_size_in_bytes
        self.self_addr = (socket.gethostbyname(socket.getfqdn()) , settings.port)

        self.peer_connections: List[connectableTCP] = []
        self.server = None
        self.current_peer = None
        self.loops_until_answer = 0
        self.current_peer_index = -1

    async def make_handshake(self, peer_addr):
        try:
            peer_reader, peer_writer = await asyncio.wait_for(asyncio.open_connection(*peer_addr), 1)
        except (TimeoutError, ConnectionRefusedError):
            return None

        peer_writer.write(
            Handshake(self.torrent.info_hash, (self.settings.user_agent + self.settings.random_id).encode()).to_bytes())
        await peer_writer.drain()
        try:
            resp = await asyncio.wait_for(peer_reader.read(68), 1)
            if not Handshake.from_bytes(resp):
                return None
            print(f"CONNECTED {peer_addr}")
            self.torrent.connection_info.connected_seeders += 1
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
            if self.loops_until_answer > 60:
                print("peer probably hanged on us, going to next peer and resetting stats")
                self.current_peer = self.get_next_peer()
                self.loops_until_answer = 0
                self.pending = False

            await self.handle_msg(self.current_peer)

            if self.piece_handler.downloading:
                self.loops_until_answer += 1
                if not self.pending:
                    await self.request_block(self.piece_handler.needed_piece_to_download_index, self.block_offset)
                    self.pending = True
                    print(
                        f"PROGRESS IN PIECE: {round(100 * self.block_offset / self.torrent.piece_size_in_bytes, 2)}")
                    print(self.block_offset, self.torrent.piece_size_in_bytes)

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
        return [item for item in res if item is not None]


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
        self.current_peer_index += 1
        print(f"returning peer index: {self.current_peer_index} ")

        if self.current_peer_index >= len(self.peer_connections):
            self.current_peer_index = 0
        return self.peer_connections[self.current_peer_index]

    def write_data_to_block(self, piece_index, block_offset, block_length, block):
        if piece_index != self.piece_handler.needed_piece_to_download_index:
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

        if self.block_offset + block_length == self.torrent.piece_size_in_bytes:
            print(f"think we downloaded")
            with open("current_piece", 'wb') as f:
                f.write(self.current_piece_data)
            if self.piece_handler.validate_piece(self.current_piece_data):
                self.piece_handler.on_validated_piece(self.current_piece_data,
                                                      self.piece_handler.needed_piece_to_download_index)
                return True

            else:
                print("piece not validated")
                return False

        return None

async def main_loop(settings, torrent_handler):
    print("running tcp download/upload loop")
    tasks = [downloadHandlerTCP(torrent, settings).main_loop() for torrent in torrent_handler.get_torrents()]

    await asyncio.gather(*tasks)