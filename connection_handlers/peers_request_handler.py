"""
Main part where we will request pieces, write them etc
"""

from torrent import Torrent
from settings.settings import Settings
import struct
import asyncio
from utils import msg_types, print_bytes_as_bits

TIMEOUT_SECS = 20
ERRORS = (AssertionError, struct.error, WindowsError, ConnectionResetError)

def pack_handshake_message(torrent, settings):
    peer_id = settings.user_agent + settings.random_id
    peer_id = peer_id.encode()
    return struct.pack(">b 19s q 20s 20s", 19, b"BitTorrent protocol", 0, torrent.info_hash, peer_id)

class requestHandler:

    def __init__(self, settings: Settings,torrent: Torrent, peer_list) -> None:
        self.torrent = torrent
        self.settings = settings
        self.peer_list = peer_list
        self.connected_peers = []
        self.bitfield = bytearray()


    async def _init_handshake_peer(self, peer_addr):
        try:
            future = asyncio.open_connection(*peer_addr)
            reader, writer = await asyncio.wait_for(future, timeout= TIMEOUT_SECS)
            writer.write(pack_handshake_message(self.torrent, self.settings))
            await writer.drain()
            future = reader.read(68)
            resp = await asyncio.wait_for(future, TIMEOUT_SECS)
            struct.unpack(">b 19s 8s 20s 20s", resp)

        except ERRORS as e:
            print(peer_addr, "invlaid peer")
            return None


        return reader, writer

    async def init_handshaken_peers(self):
        handshaken_peers_tasks = [self._init_handshake_peer(peer_addr) for peer_addr in self.peer_list]
        handshaken_peers = await asyncio.gather(*handshaken_peers_tasks)
        self.connected_peers = [handshaken_peer for handshaken_peer in handshaken_peers if handshaken_peer]

        print(len(self.peer_list), len(self.connected_peers))

        asking_bit_field_tasks = [self.get_bitfield_from_peers(*socket) for socket in self.connected_peers]
        available_bitfield_peers = await asyncio.gather(*asking_bit_field_tasks)
        self.connected_peers = [available_bitfield_peer for available_bitfield_peer in available_bitfield_peers if available_bitfield_peer]
        
        print(len(self.peer_list), len(self.connected_peers))
        
        asking_pieces_tasks = [self.download_piece(*connected_peer) for connected_peer in self.connected_peers]
        await asyncio.gather(*asking_pieces_tasks)


    async def get_bitfield_from_peers(self, reader, writer):
        needed_pieces = gen_bitfield(self.torrent)
        bitfield_struct = pack_bitfield_struct(needed_pieces)

        try:
            writer.write(bitfield_struct)
            await writer.drain()
            future = reader.read(4)
            msg_len = await asyncio.wait_for(future, TIMEOUT_SECS)
            msg_len = struct.unpack("> I ", msg_len)[0]
            future = reader.read(msg_len - 4)
            msg_data = await asyncio.wait_for(future, TIMEOUT_SECS)
            msg_id = msg_data[0]
            assert msg_id == msg_types.bitfield
        except ERRORS:
            writer.close()
            # await writer.wait_closed()
            return None


        available_bitfield = msg_data[1:]
        if not available_bitfield:
            writer.close()
            # await writer.wait_closed()
            return None

        return reader, writer, available_bitfield
                


    async def download_piece(self, reader, writer, bitfield):
        piece_index = 0 
        while not is_available_piece(bitfield, piece_index):
            piece_index+= 1
        # when we are here we have a piece index of available piece


        interseted_struct = struct.pack('> i b', 5, msg_types.interested)
        try:
            writer.write(interseted_struct)
            future =  writer.drain()
            await asyncio.wait_for(future, TIMEOUT_SECS)

        except ERRORS:
            return None

        while True:
            # assuming peer knows we are interested its a ping-pong game where we listen to him and he listens to us.
            try:
                msg_len = reader.read(4)
                # we may get choke messages, we will wait for unchoke.
                msg_len = await asyncio.wait_for(msg_len, None)
                assert len(msg_len) == 4
                msg_len = struct.unpack('> I', msg_len)[0]
                data = reader.read(msg_len - 4)
                data = await asyncio.wait_for(data, TIMEOUT_SECS)
                msg_id = data[0]

                print("msg_id:", msg_id)
                assert len(data) == msg_len - 4

            except ERRORS as e:
                print(e)
                writer.close()
                # await writer.wait_closed()
                print("sorry, writer is busted")
                return None

            

            msg_id = data[0]
            data = data[1:]




# in the future that function will be a part of Torrent post init. it will contain all pieces hashes and the missing pieces as 0s in bitfield
def gen_bitfield(torrent: Torrent):
    # pieces_amount = len(torrent.pieces_info.pieces_hashes)
    # num_bytes_on = pieces_amount // 8
    # last_byte_bits_on = pieces_amount % 8

    # bitfield_byte_object = bytes([0xff]*num_bytes_on)

    # if last_byte_bits_on != 0:
    #     byte = (0xff << last_byte_bits_on) & 0xff
    #     bitfield_byte_object += bytes([byte])

    # return bitfield_byte_object

    return bytes([0]) * len(torrent.pieces_info.pieces_hashes)

def pack_bitfield_struct(bitfield):
    # 4 bytes -> messeage len
    # 1 byte -> message id
    # rest - optional payload (in this case: each byte represents 8 pieces we ask for)
    msg_id = msg_types.bitfield
    total_msg_len = 4 + 1 + len(bitfield) 
    return struct.pack(f'> i b {len(bitfield)}s', total_msg_len, msg_id, bitfield)

def is_available_piece(bitfield, piece_index):
    byte_index = piece_index // 8
    bit_in_byte_index = piece_index % 8

    byte_to_look_at = bitfield[byte_index]
    mask = 1 << bit_in_byte_index

    return byte_to_look_at & mask

def pack_piece_request_struct(torrent: Torrent, piece_index):
    begin = 0
    length = torrent.pieces_info.piece_size
    msg_length = 17

    # length msg = 17 bytes total.
    # id msg (1) one byte
    # piece index = 4 bytes
    # piece begin = 4 bytes
    # length = 4 bytes

    # currently piece begin is 0 and length is whole piece size, so each request is for one piece

    return struct.pack('> i b i i i', msg_length, msg_types.request, piece_index, begin, length)

async def send_unchoke(writer):
    unchoke_struct = struct.pack('> i b', 5, msg_types.unchoke)
    try:
        writer.write(unchoke_struct)
        await writer.drain()

    except ConnectionResetError:
        return None

        


async def request_piece(writer, torrent, piece_index):
    piece_request_payload = pack_piece_request_struct(torrent, piece_index)
    writer.write(piece_request_payload)
    await writer.drain()
    print("requested piece", piece_index)
 

# if successful download - return buffer, else return 0
async def try_to_download_piece(writer, reader, torrent, piece_index):
    # we will send an interested message, and once we get "unchoke" we will asks for pieces.
    # we also need to make sure to send "unchoke" ourselves everytime peer sends "interested"


    try:
        while True:
            while True:
                data = await reader.read(4)
                if len(data) < 4:
                    await asyncio.sleep(0.1)
                    continue
                break

            data_len = struct.unpack('> I', data)[0]
            while True:
                data = await reader.read(data_len - 4) # we already read 5 bytes so we need ro sub it from data len
                if len(data) < 4:
                    await asyncio.sleep(0.1)
                    continue
                break

            msg_id = data[0]
            new_data_to_be_used = data[1:]

            print(msg_id, new_data_to_be_used)

            if msg_id == msg_types.interested:
                print("got interested, sent unchoke")
                await send_unchoke(writer)

            elif msg_id == msg_types.unchoke:
                # send a payload with details about the piece we want
                print("got unchoke, sent interested")
                await request_piece(writer, torrent, piece_index)

            elif msg_id == msg_types.piece:
                print("GOT PIECE")
                exit(-1)

            elif msg_id == msg_types.have:
                print("got have message")
                continue

            elif msg_id == msg_types.choke:
                print("got choke")
                await asyncio.sleep(1)

            else:
                print("got unrecognzied id:", msg_id)

    except ConnectionResetError:
        print("CONNECTION ERROR")
        await asyncio.sleep(10)



# will arrange us a dict where each key is an index, which value is a list of peers we can ask for a piece. returns an error if not all pieces are covered. 
# we will sort the dict from high to low 
def map_bitfields():
    pass







    
# get a peer list, a torrent; try to connect to one peer
async def connect_to_single_peer(torrent: Torrent, peers_list, settings: Settings):
    packed = pack_handshake_message(torrent, settings)
    possible_handshakes_connections = [_try_to_handshake(peer, packed) for peer in peers_list] #
    results = await asyncio.gather(*possible_handshakes_connections)

    results = [result for result in results if result]

    download_tries = [try_to_download_from(result, torrent) for result in results]

    await asyncio.gather(*download_tries)
