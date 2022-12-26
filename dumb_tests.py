from bencoding import *

with open('manjaro-kde-21.3.7-220816-linux515.iso.torrent', 'rb') as f:
    content = f.read()



x = decode(content)[0]
print(x.keys())