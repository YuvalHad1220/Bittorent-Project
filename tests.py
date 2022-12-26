import unittest
from bencoding import *
from dataclasses import dataclass
import string, random
from utils import sizes, return_piece_size
from dctodb import dctodb
import datetime
global_db_filename = "tests.db"

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


class TestDcToDbBasic(unittest.TestCase):
    @dataclass
    class Test:
        name: str
        some_bytes: bytes
        index: int = 0

    @classmethod
    def setUpClass(cls):
        cls.test_db: dctodb = dctodb(TestDcToDbBasic.Test, global_db_filename)


    def test_basic_insert(self):
        """
        Asserting that after insertion we get our rows (indexes) correctly. This ensures that the insertion was working.

        """
        row_count_in_table = self.test_db._get_count() # we want row amount before insertion

        test_obj_lis = [self.Test("yuval", b'yuvalhahaha') for _ in range(random.randint(1, 10))]
        TestDcToDbBasic.test_db.insert(*test_obj_lis)
        for i, test_obj in enumerate(test_obj_lis, 1 + row_count_in_table):
            self.assertEqual(i, test_obj.index)

    def test_basic_fetching_all(self):
        res = TestDcToDbBasic.test_db.fetch_all()
        self.assertEqual(len(res), self.test_db._get_count())

    # def test_basic_update(self):
    #     pass

    # def test_basic_delete(self):
    #     pass

    # def test_basic_fetch_where(self):
    #     pass

class TestDcToDbWithSubclass(unittest.TestCase):
    @dataclass
    class SubDc:
        is_sub_cls: bool
        datetime_works: datetime.datetime

    @classmethod
    def setUpClass(cls):
        cls.test_db: dctodb = dctodb(TestDcToDbBasic.Test, global_db_filename)

    def test_with_sub_dc_insert(self):
        pass

    def test_with_sub_dc_fetching_all(self):
        pass

    def test_with_sub_dc_update(self):
        pass

    def test_with_sub_dc_delete(self):
        pass

    def test_with_list_insert(self):
        pass

    def test_with_list_fetching_all(self):
        pass

    def test_with_list_update(self):
        pass

    def test_with_list_delete(self):
        pass

    def test_with_list_of_dcs_insert(self):
        pass

    def test_with_list_of_dcs_fetching_all(self):
        pass

    def test_with_list_of_dcs_update(self):
        pass

    def test_with_list_of_dcs_delete(self):
        pass
if __name__ == "__main__":
    unittest.main()
