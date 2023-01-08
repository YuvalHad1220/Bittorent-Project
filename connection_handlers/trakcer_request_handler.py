"""
Will handle announcements to the tracker weather its via http requests or udp
"""
import aiohttp
from torrent import Torrent
from typing import List

# A thread should start that def:
async def main():
    pass



# splits announcements to torrentx(supports multiple announcements at once) and regular torrent files
def _split_torrentx_regular(to_announce_list):
    pass

# splits announcements to udp and http trackers. both torrentx and regular can support both
def _split_udp_http(to_announce_list):
    pass


"""
All of these function should reduce to a couple of functions: announce_udp, announce_http, announce_multiple_udp, announce_multiple_http
"""

async def announce_start_http(aiohttp_client: aiohttp.ClientSession, *torrents: List[Torrent]):
    pass

async def _announce_legacy_start_http(aiohttp_client: aiohttp.ClientSession, *torrents: List[Torrent]):
    HTTP_HEADERS = {
        "Accept-Encoding": "gzip",
        "User-Agent": client.user_agent
    }

    HTTP_PARAMS = {
        "info_hash": urllib.parse.quote_from_bytes(torrent.info_hash),
        "peer_id": client.peer_id + client.rand_id,
        "port": client.port,
        "uploaded": int(torrent.uploaded),
        "downloaded": int(torrent.downloaded),
        "left": int(torrent.size - torrent.downloaded),
        "event": 
        "compact": 1,
        "numwant": 200,
        "supportcrypto": 1,
        "no_peer_id": 1
    }

    async with aiohttp_client.get(url= torrents.announce_url, headers = HTTP_HEADERS) as resp:
        content = await resp.read()
        info = decode(content)

        update_decoded(info, torrent)

async def _announce_legacy_start_udp():
    pass

async def _announce_legacy_resume_http():
    pass

async def _announce_legacy_resume_udp():
    pass

async def _announce_legacy_finish_http():
    pass

async def _announce_legacy_finish_udp():
    pass

async def announce_start_udp(*instances):
    pass

async def announce_resume_http(aiohttp_client,*instances):
    pass

async def announce_resume_udp(*instances):
    pass

async def announce_finish_http(aiohttp_client,*instances):
    pass

async def announce_finish_udp(*instances):
    pass