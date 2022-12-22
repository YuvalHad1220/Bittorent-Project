import unittest
from bencoding import encode, decode
import random, string


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

    def test_encoding_decoding(self):
        # we need to test a dictionary that contain dictonaries, a list that contains lists and so on
        
        test_list = TestBencode.gen_random_list()
        
        encoded = encode(test_list)

        decoded = decode(encoded)[0]
        print(encoded)
        print('------------------------')
        print(decoded)
        print('------------------------')
        print(test_list)
        
        self.assertEqual(str(test_list), str(decoded))

if __name__ == "__main__":
    unittest.main()