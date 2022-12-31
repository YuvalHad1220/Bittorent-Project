import unittest
from bencoding import *
import string
from utils import *
from torrent import Torrent, create_torrent
from dctodb import dctodb
import time

class TestBencode(unittest.TestCase):

    def test_str(self):
        _str = string.printable
        res = decode(encode(_str))[0]
        expected = _str.encode()
        self.assertEqual(expected, res)


    def test_int(self):
        _int = 87259802375690842576903487
        expected = _int
        res = decode(encode(_int))[0]
        self.assertEqual(expected, res)

    def test_dict(self):
        _dict = {
            "yuval": 4,
            "4": 4,
            "239048": "234234",
            "8v hjbngyum, bnw34er eeeeeddddiiiiiillllll": 234234,
            234: 234234,
            2365: "324234"
        }

        res = decode(encode(_dict))[0]

        excepted = {
            b"yuval": 4,
            b"4": 4,
            b"239048": b"234234",
            b"8v hjbngyum, bnw34er eeeeeddddiiiiiillllll": 234234,
            234: 234234,
            2365: b"324234"
        }

        self.assertEqual(excepted, res)

    def test_list(self):
        _list = [
            {
            "yuval": 4,
            "4": 4,
            "239048": "234234",
            "8v hjbngyum, bnw34er eeeeeddddiiiiiillllll": 234234,
            234: 234234,
            2365: "324234"
        },
        123213, string.printable, [1,4,2, "34234", b'234234'],
        b'234234234', "yuvalon", "lolo.lolsdf0298490289080908990{dict:testesdf}ff",
        [[[[[[[[['3'],'b']]],3],3,4,5],{"f":"t"}]]]
        ]

        res = decode(encode(_list))[0]

        excepted = [
            {
            b"yuval": 4,
            b"4": 4,
            b"239048": b"234234",
            b"8v hjbngyum, bnw34er eeeeeddddiiiiiillllll": 234234,
            234: 234234,
            2365: b"324234"
        },
        123213, string.printable.encode(), [1,4,2, b"34234", b'234234'],
        b'234234234', b"yuvalon", b"lolo.lolsdf0298490289080908990{dict:testesdf}ff",
        [[[[[[[[[b'3'],b'b']]],3],3,4,5],{b"f":b"t"}]]]
        ]

        self.assertEqual(excepted, res)
        
class TestUtils(unittest.TestCase):
    def test_piece_size(self):
        # we want to make sure we get smallest pieces size available
        file_size_to_256kib = (
            256 * sizes["Kib"] * 5 * sizes["MiB"] - 1
        )  # until here it will always be 256kilobibits to have less than 15MiB
        file_size_to_512kib = (
            256 * sizes["Kib"] * 5 * sizes["MiB"] - 1
        )  # until here it will always be 512 kib
        file_size_to_1mib = 1 * sizes["Mib"] * 5 * sizes["MiB"] - 1  # same thing...
        file_size_to_2mib = (
            2 * sizes["Mib"] * 5 * sizes["MiB"] - 1
        )  # until here it will always be 512
        file_size_to_4mib = (
            4 * sizes["Mib"] * 5 * sizes["MiB"] - 1
        )  # until here it will always be 512
        file_size_to_8mib = (
            8 * sizes["Mib"] * 5 * sizes["MiB"] - 1
        )  # until here it will always be 512
        file_size_to_16mib = (
            16 * sizes["Mib"] * 5 * sizes["MiB"] - 1
        )  # until here it will always be 512
        file_size_to_32mib = (
            32 * sizes["Mib"] * 5 * sizes["MiB"] - 1
        )  # until here it will always be 512

        """
        All of those pieces size should result to <= 41943040 pieces. Obviously that algorithm needs much more improvment but it's a start
        """

        self.assertAlmostEqual(
            file_size_to_256kib / return_piece_size(file_size_to_256kib)["size"],
            41943040,
            places=4,
        )
        self.assertAlmostEqual(
            file_size_to_512kib / return_piece_size(file_size_to_512kib)["size"],
            41943040,
            places=4,
        )
        self.assertAlmostEqual(
            file_size_to_1mib / return_piece_size(file_size_to_1mib)["size"],
            41943040,
            places=4,
        )
        self.assertAlmostEqual(
            file_size_to_2mib / return_piece_size(file_size_to_2mib)["size"],
            41943040,
            places=4,
        )
        self.assertAlmostEqual(
            file_size_to_4mib / return_piece_size(file_size_to_4mib)["size"],
            41943040,
            places=4,
        )
        self.assertAlmostEqual(
            file_size_to_8mib / return_piece_size(file_size_to_8mib)["size"],
            41943040,
            places=4,
        )
        self.assertAlmostEqual(
            file_size_to_16mib / return_piece_size(file_size_to_16mib)["size"],
            41943040,
            places=4,
        )
        self.assertAlmostEqual(
            file_size_to_32mib / return_piece_size(file_size_to_32mib)["size"],
            41943040,
            places=4,
        )

class TestDCtoDB(unittest.TestCase):
    """
    We will use our torrent classes. As long as we can fetch a torrent and its subitems, than all is good
    """
    db_path = "torrentTest.db"
    def test_for_table_creation(self):
        dctodb(Torrent, self.db_path)
        # if no error is raised everything is good


    """
    INSERTION TIME MEASUREMENT:
    1st iteration - no edits, no transcation (creating connection to db every function): 19.26 SECONDS

    
    """
    def test_insert(self):
        with open("test.torrent", 'rb') as f:
            content = f.read()
        torrent_obj = create_torrent("added_torrent_files",content, "download_folder", False)

        torrent_db = dctodb(Torrent, self.db_path)
        start_time = time.time()
        torrent_db.insert_one(torrent_obj)
        end_time = time.time()
        print("INSERTION TIME: ", end_time-start_time)
        self.assertEqual(torrent_db._get_count(), torrent_obj.index)
    def test_fetch_where(self):
        with open("test.torrent", 'rb') as f:
            content = f.read()
        torrent_obj = create_torrent("added_torrent_files",content, "download_folder", False)
        torrent_db = dctodb(Torrent, self.db_path)
        torrent_db.insert_one(torrent_obj)

        fetched = torrent_db.fetch_where(f'id = {torrent_obj.index}')[0] 
        self.assertDictEqual(torrent_obj.asdict(), fetched.asdict())

    def test_fetch_all(self):
        torrent_db = dctodb(Torrent, self.db_path)
        total_items = torrent_db._get_count()

        fetched = torrent_db.fetch_all()

        self.assertEqual(total_items, len(fetched))


if __name__ == "__main__":
    unittest.main()
