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


async def piece_communication(writer, reader, torrent, piece_index):
    piece_request_payload = pack_piece_request_struct(torrent, piece_index)
    print("now we are communicating to get piece", piece_index)

    writer.write(piece_request_payload)
    await writer.drain()

    print("requested all piece", piece_index)
    while True:
        data = await reader.read(5)
        if data == b"":
            print("null data")
            await asyncio.sleep(0.01)
            continue

        data_len = data[0:4]
        msg_id = data[4]
        print("got response of type", msg_id)
        break
async def send_unchoke(writer):
    unchoke_struct = struct.pack('> i b', 5, msg_types.unchoke)
    writer.write(unchoke_struct)
    await writer.drain()

async def send_interested(writer):
    interseted_struct = struct.pack('> i b', 5, msg_types.interested)
    writer.write(interseted_struct)
    await writer.drain()

# if successful download - return buffer, else return 0
async def try_to_download_piece(writer, reader, torrent, piece_index):
    # we will send an interested message, and once we get "unchoke" we will asks for pieces.
    # we also need to make sure to send "unchoke" ourselves everytime peer sends "interested"

    await send_interested(writer)
    print("sent interested to peer now waiting for msg")

    while True:
        data = await reader.read(5)
        if data == b"":
            await asyncio.sleep(0.01)
            continue

        data_len = data[0:4]
        msg_id = data[4]
        print("msg recieved and its id is", msg_id)

        if msg_id == msg_types.interested:
            await send_unchoke(writer)

        if msg_id == msg_types.unchoke:
            # send a payload with details about the piece we want
            await piece_communication(writer, reader, torrent, piece_index)

        break


    pass




async def ask_for_bitfield(torrent: Torrent, writer, reader):
    needed_pieces = gen_bitfield(torrent)
    bitfield_struct = pack_bitfield_struct (needed_pieces)
    writer.write(bitfield_struct)
    await writer.drain()
    avaiable_bitfields = await parse_and_read_message(reader, msg_types.bitfield)
    
    print("got bitfield as response")

    for piece_index in range(len(torrent.pieces_info.pieces_hashes)):
        if not is_available_piece(avaiable_bitfields, piece_index):
            print("not available")

        else:
            print("now trying to request for piece index", piece_index)
            await try_to_download_piece(writer, reader,torrent, piece_index)


    exit()
# will arrange us a dict where each key is an index, which value is a list of peers we can ask for a piece. returns an error if not all pieces are covered. 
# we will sort the dict from high to low 
def map_bitfields():
    pass






