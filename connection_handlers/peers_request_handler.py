"""
Main part where we will request pieces, write them etc
"""

from torrent import Torrent
from settings.settings import Settings
import struct
import asyncio
from utils import msg_types, print_bytes_as_bits

def unpack_handshake_message(message):
    try:
        return struct.unpack(">b 19s 8s 20s 20s", message)

    except struct.error:
        return None
    
def pack_handshake_message(torrent, settings):
    peer_id = settings.user_agent + settings.random_id
    peer_id = peer_id.encode()
    return struct.pack(">b 19s q 20s 20s", 19, b"BitTorrent protocol", 0, torrent.info_hash, peer_id)

async def _try_to_handshake(peer_address, message):
    reader, writer = await asyncio.open_connection(*peer_address)
    writer.write(message)
    await writer.drain()
    try:
        data = await reader.read(68)
        data = unpack_handshake_message(data)
        if data:
            return writer, reader
        else:
            return None
    except asyncio.TimeoutError:
        return None

# get a peer list, a torrent; try to connect to one peer
async def connect_to_single_peer(torrent: Torrent, peers_list, settings: Settings):
    packed = pack_handshake_message(torrent, settings)
    possible_handshakes_connections = [_try_to_handshake(peer, packed) for peer in peers_list] #

    # as soon as we're connected to a peer, break out and cancel all other tasks
    for task in asyncio.as_completed(possible_handshakes_connections):
        returned_value = await task
        if returned_value:
            break


    writer, reader = returned_value
    await ask_for_bitfield(torrent, writer, reader)
    writer.close()

async def parse_and_read_message(reader, expected_type):
    # 4 first bytes are length
    # 5th byte is type
    res = await reader.read(4)
    msg_len = struct.unpack(">I", res)[0] # unpack the message length
    data = await reader.read(msg_len) # receive the rest of the message
    msg_id = data[0] 

    if msg_id == expected_type:
        return data[1:]

    else:
        print("not expected type")
        exit()

# in the future that function will be a part of Torrent post init. it will contain all pieces hashes and the missing pieces as 0s in bitfield
def gen_bitfield(torrent: Torrent):
    pieces_amount = len(torrent.pieces_info.pieces_hashes)
    num_bytes_on = pieces_amount // 8
    last_byte_bits_on = pieces_amount % 8

    bitfield_byte_object = bytes([0xff]*num_bytes_on)

    if last_byte_bits_on != 0:
        byte = (0xff << last_byte_bits_on) & 0xff
        bitfield_byte_object += bytes([byte])

    return bitfield_byte_object

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


async def ask_for_bitfield(torrent: Torrent, writer, reader):
    needed_pieces = gen_bitfield(torrent)
    bitfield_struct = pack_bitfield_struct (needed_pieces)
    writer.write(bitfield_struct)
    await writer.drain()

    avaiable_bitfields = await parse_and_read_message(reader, msg_types.bitfield)
    for piece_index in range(len(torrent.pieces_info.pieces_hashes)):
        if not is_available_piece(avaiable_bitfields, piece_index):
            print("not available")

        else:
            await try_to_download_piece(writer, reader, )


    exit()
# will arrange us a dict where each key is an index, which value is a list of peers we can ask for a piece. returns an error if not all pieces are covered. 
# we will sort the dict from high to low 
def map_bitfields():
    pass






