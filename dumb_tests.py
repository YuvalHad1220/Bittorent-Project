# from bencoding import *
# from torrent import torrent_pieces


# with open('manjaro-kde-21.3.7-220816-linux515.iso.torrent', 'rb') as f:
#     content = f.read()


from dataclasses import dataclass
import datetime
from dctodb import dctodb

@dataclass 
class sub_class:
    date: datetime.datetime
    index: int = 0

    
@dataclass
class mainClass:
    name: str
    age: int
    sub: sub_class

    index: int = 0

mainclass_db = dctodb(mainClass, "Test.db")

mainobj = mainClass("yuvi", 23, sub_class(datetime.datetime.now()))
mainclass_db.insert_one(mainobj)
# print(mainobj.index)