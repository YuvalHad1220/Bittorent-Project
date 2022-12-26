from bencoding import *
from torrent import torrent_pieces


with open('manjaro-kde-21.3.7-220816-linux515.iso.torrent', 'rb') as f:
    content = f.read()
