"""
Main part where we will request pieces, write them etc
"""

from torrent import Torrent
from settings.settings import Settings
import struct
import asyncio
from utils import msg_types



async def read_message(reader):
    # 4 first bytes are length
    # 5th byte is type

    res = await reader.read(4)
    msg_len = struct.unpack(">I", res)[0] # unpack the message length
    data = await reader.read(msg_len) # receive the rest of the message
    msg_id = data[0] 

    if msg_id == msg_types.bitfield:
        return data[1:]



async def ask_bitfield(torrent: Torrent, writer, reader):
    pieces_amount = len(torrent.pieces_info.pieces_hashes)
    num_bytes_on = pieces_amount // 8
    last_byte_bits_on = pieces_amount % 8

    bitfield_byte_object = bytes([0xff]*num_bytes_on)

    if last_byte_bits_on != 0:
        byte = (0xff << last_byte_bits_on) & 0xff
        bitfield_byte_object += bytes([byte])

    msg_id = msg_types.bitfield
    total_msg_len = 4 + 1 + len(bitfield_byte_object) 
    # 4 bytes -> messeage len
    # 1 byte -> message id
    # rest - optional payload (in this case: each byte represents 8 pieces we ask for)
    packed_struct = struct.pack(f'> i b {len(bitfield_byte_object)}s', total_msg_len, msg_id, bitfield_byte_object)
    asking_pieces_str = ''.join(['{:08b}'.format(b) for b in packed_struct])

    writer.write(packed_struct)
    await writer.drain()
    avaiable_bitfields = await read_message(reader)
    print(avaiable_bitfields)
    print(bitfield_byte_object)
    avaiable_pieces_str = ''.join(['{:08b}'.format(b) for b in avaiable_bitfields])

    print("peer has sent a relevant result. now we want to compare which pieces it has and which not")

    # we want to run on the min length, as we sending padded bits in our request but peer does not send padded bits in his response
    for i in range(min(len(avaiable_pieces_str), len(asking_pieces_str))):
        if avaiable_bitfields[i] != bitfield_byte_object[i] and avaiable_bitfields[i] == "0":
            print(f"peer doesnt have piece {i}")
        else:
            print(f"peer have piece {i}")

# will arrange us a dict where each key is an index, which value is a list of peers we can ask for a piece. returns an error if not all pieces are covered. 
# we will sort the dict from high to low 
def map_bitfields():
    pass

def parse_valid_handhshake(message):
    try:
        return struct.unpack(">b 19s 8s 20s 20s", message)

    except struct.error:
        return None
    


async def _get_piece(peer_address, message):
    reader, writer = await asyncio.open_connection(*peer_address)

    # if a message is of type "i have then we stop the loop"
    while True:
        # we will async send message and async wait for a message
        # if we get a valid message (we need to parse it) then we return
        writer.write(message)
        await writer.drain()
        try:
            data = await reader.read(68)
            data = parse_valid_handhshake(data)
            if data:
                return writer, reader

        except asyncio.TimeoutError:
            # no problem. we will try again and again. When a peer is available we exit the loop anyways
            await asyncio.sleep(5)



async def get_piece(torrent: Torrent, piece_index, peers_list, settings: Settings):
    # we want to run tasks of every peer until we get a response. when we get a response we will close the loop and return value
    # when _get_piece is returned, cancel all other tasks and then we can return
    # in the future we need to make the system smarter, i.e we cant rely on just ONE peer to get all bitfields.
    peer_id = settings.user_agent + settings.random_id
    peer_id = peer_id.encode()

    packed = struct.pack(">b 19s q 20s 20s", 19, b"BitTorrent protocol", 0, torrent.info_hash, peer_id)

    tasks_for_piece = [_get_piece(peer, packed) for peer in peers_list] #
    for task in asyncio.as_completed(tasks_for_piece):
        returned_value = await task
        if returned_value:
            writer, reader = returned_value
            await ask_bitfield(torrent, writer, reader)
            writer.close()
            exit()
