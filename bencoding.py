"https://shekhargulati.com/2020/09/19/writing-bencode-parser-in-kotlin/"

from typing import List,Dict,Tuple,Any

def encode(item) -> bytes:
    if isinstance(item, str):
        return f"{len(item)}:{item}".encode()

    if isinstance(item, int):
        return f"i{item}e".encode()

    if isinstance(item, list):
        # for every item in list we need to encode
        st = b"l"
        st += b"".join([encode(item_in_list) for item_in_list in item])
        st += b"e"
        return st

    if isinstance(item, dict):
        st = b"d"
        st += b"".join([encode(key) + encode(value) for key, value in item.items()])
        st += b"e"
        return st

    if isinstance(item, bytes):
        st = f"{len(item)}:".encode() + item
        return st


def decode_str_or_bytes(encoded_bytes) -> Tuple[bytes, int]:
    "4:spam........."
    str_len = encoded_bytes.split(b":")[0]
    digits_in_str = len(str_len)
    str_len = int(str_len)
    str_itself = encoded_bytes[digits_in_str + 1 : digits_in_str + 1 + str_len]
    return str_itself, digits_in_str + 1 + str_len


def decode_int(encoded_bytes) -> Tuple[int, int]:
    "i8e........"
    # we will find the first index of e
    index_of_e = encoded_bytes.find(b"e")
    return int(encoded_bytes[1:index_of_e]), index_of_e + 1


def decode_list(encoded_bytes) -> Tuple[List[Any], int]:
    "li8e4:spame......."
    lis = []
    index = 1  # we know that index 0 is l, so starting from nex one
    while index < len(encoded_bytes):
        current_char = encoded_bytes[index]
        if current_char == ord(b"e"):
            # we finished iterating over the list, no point iterating over more
            # we will just update the index before
            index += 1
            break
        decoded_val, index_to_update = decode(encoded_bytes[index:])
        lis.append(decoded_val)
        index += index_to_update

    return lis, index


def decode_dict(encoded_bytes) -> Tuple[Dict[Any,Any]]:
    "d3:key5value:li8e4:spame......."

    dic = dict()
    index = 1  # we know that index 0 is l, so starting from nex one
    while index < len(encoded_bytes):
        current_char = encoded_bytes[index]
        if current_char == ord(b"e"):
            # we finished iterating over the dict, no point iterating over more
            # we will just update the index before
            index += 1
            break
        decoded_val_as_key, index_to_update = decode(encoded_bytes[index:])
        index += index_to_update
        decoded_val_as_value, index_to_update = decode(encoded_bytes[index:])
        index += index_to_update
        dic[decoded_val_as_key] = decoded_val_as_value

    return dic, index


def decode(encoded_bytes) -> Tuple[Any, int]:
    current_char = encoded_bytes[0]
    if current_char == ord(b"i"):
        return decode_int(encoded_bytes)
    if current_char == ord(b"l"):
        return decode_list(encoded_bytes)

    if current_char == ord(b"d"):
        return decode_dict(encoded_bytes)
        
    # default, meaning its string\bytes
    return decode_str_or_bytes(encoded_bytes)




if __name__ == "__main__":
    dic = {
        "name": "yuval",
        "age": [1,"123",1, {"yuvali":"yes"}]
    }

    encoded = encode(dic)
    print(decode(encoded))