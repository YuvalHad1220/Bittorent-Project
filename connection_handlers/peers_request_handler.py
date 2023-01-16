"""
Main part where we will request pieces, write them etc
"""

from torrent import Torrent
from settings.settings import Settings
import struct
import asyncio
from utils import msg_types

async def ask_bitfield(torrent: Torrent, peer_address):
    reader, writer = await asyncio.open_connection(*peer_address)

    pieces_len = len(torrent.pieces_info.pieces_hashes)

    msg = struct.pack()





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
                writer.close()
                return data

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
            print(returned_value)
            print("got piece, now we need to send for everyone else a cancel, i.e drop the loop and send again")
            exit(-1)