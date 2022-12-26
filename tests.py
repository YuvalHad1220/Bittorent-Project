import unittest
from bencoding import *
import random, string
from utils import sizes, return_piece_size


class TestBencode(unittest.TestCase):
    def gen_random_list():
        # in list we want to be dicts, ints, strs randomly.
        dicts_amount = random.randint(0,64) + 1
        int_amount = random.randint(0,64) + 1
        str_amount = random.randint(0,64) + 1

        to_ret = [TestBencode.gen_random_dict() for _ in range(dicts_amount)] + [TestBencode.gen_random_int() for _ in range(int_amount)] + [TestBencode.gen_random_str() for _ in range(str_amount)]
        random.shuffle(to_ret)
        return to_ret


    def gen_random_int():
        return random.randint(-64,64)

    def gen_random_str():
        letters = string.printable # characters that are considered printable. This is a combination of constants digits, letters, punctuation, and whitespace.
        return ''.join(random.choice(letters) for _ in range(random.randint(0,64)))

    def gen_random_dict():
        # we want random int or str as keys. we want random int, str, lists as values

        dic = dict()
        int_keys = [TestBencode.gen_random_int() for _ in range(random.randint(0,64) + 1)]
        str_keys = [TestBencode.gen_random_str() for _ in range(random.randint(0,64) + 1)]

        for key in int_keys + str_keys:
            chosen = random.randint(1,2)
            val = None
            match chosen:
                case 1:
                    val = TestBencode.gen_random_str()
                    break
                case 2:
                    val = TestBencode.gen_random_int()

            dic[key] = val

        return dic

    def test_str(self):
        _str = "yuvali"

        encoded = encode(_str)
        res = decode(encoded)[0].decode()
        self.assertEqual(_str, res)

    def test_int(self):
        _int = 5
        encoded = encode(_int)
        self.assertEqual(_int, decode(encoded)[0])
        
    # def test_list(self):
    #     _list = [1,2,4,"yuv",[1,2,3,4]]
    #     encoded = encode(_list)
    #     self.assertEqual(_list, decode(encoded)[0])

    # def test_dict(self):
    #     _dict = {
    #         "yuvali": 4,
    #         "test": [1,2,3,4],
    #         "lol": "lol",
    #         3: 23423
    #     }

        # encoded = encode(_dict)
        # self.assertEqual(_dict, decode(encoded)[0])



    def test_encoding_decoding(self):
        # we need to test a dictionary that contain dictonaries, a list that contains lists and so on
        
        test_list = TestBencode.gen_random_list()
        
        encoded = encode(test_list)

        decoded = decode(encoded)[0]

        self.assertEqual(str(test_list), str(decoded))


class testUtils(unittest.TestCase):
    def test_piece_size(self):
        # we want to make sure we get smallest pieces size available
        file_size_to_256kib = 256 * sizes['Kib'] * 5 * sizes['MiB'] - 1 # until here it will always be 256kilobibits to have less than 15MiB
        file_size_to_512kib =  256 * sizes['Kib'] * 5 * sizes['MiB']  - 1 # until here it will always be 512 kib
        file_size_to_1mib =  1 * sizes['Mib'] * 5 * sizes['MiB']  - 1 # same thing...
        file_size_to_2mib =  2 * sizes['Mib'] * 5 * sizes['MiB']  - 1 # until here it will always be 512
        file_size_to_4mib =  4 * sizes['Mib'] * 5 * sizes['MiB']  - 1 # until here it will always be 512
        file_size_to_8mib =  8 * sizes['Mib'] * 5 * sizes['MiB']  - 1 # until here it will always be 512
        file_size_to_16mib =  16 * sizes['Mib'] * 5 * sizes['MiB']  - 1 # until here it will always be 512
        file_size_to_32mib =  32 * sizes['Mib'] * 5 * sizes['MiB']  - 1 # until here it will always be 512

        """
        All of those pieces size should result to <= 41943040 pieces. Obviously that algorithm needs much more improvment but it's a start
        """


        self.assertAlmostEqual(file_size_to_256kib / return_piece_size(file_size_to_256kib)['size'], 41943040, places=4)
        self.assertAlmostEqual(file_size_to_512kib / return_piece_size(file_size_to_512kib)['size'], 41943040, places=4)
        self.assertAlmostEqual(file_size_to_1mib / return_piece_size(file_size_to_1mib)['size'], 41943040, places=4)
        self.assertAlmostEqual(file_size_to_2mib / return_piece_size(file_size_to_2mib)['size'], 41943040, places=4)
        self.assertAlmostEqual(file_size_to_4mib / return_piece_size(file_size_to_4mib)['size'], 41943040, places=4)
        self.assertAlmostEqual(file_size_to_8mib / return_piece_size(file_size_to_8mib)['size'], 41943040, places=4)
        self.assertAlmostEqual(file_size_to_16mib / return_piece_size(file_size_to_16mib)['size'], 41943040, places=4)
        self.assertAlmostEqual(file_size_to_32mib / return_piece_size(file_size_to_32mib)['size'], 41943040, places=4)



        



if __name__ == "__main__":
    unittest.main()