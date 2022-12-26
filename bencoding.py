"https://shekhargulati.com/2020/09/19/writing-bencode-parser-in-kotlin/"

def encode(item) -> bytes:
    if isinstance(item, str):
        return f"{len(item)}:{item}".encode()

    if isinstance(item, int):
        return f"i{item}e".encode()

    if isinstance(item, list):
        # for every item in list we need to encode
        st = b"l"
        st+= b''.join([encode(item_in_list) for item_in_list in item])
        st+= b"e"
        return st
    
    if isinstance(item, dict):
        st = b"d"
        st+= b''.join([encode(key)+encode(value) for key,value in item.items()])
        st += b"e"
        return st

    if isinstance(item, bytes):
        st = f"{len(item)}:".encode() + item
        return st


def decode_str(encoded_bytes):
    "4:spam........."
    str_len = encoded_bytes.split(b':')[0]
    digits_in_str = len(str_len)
    str_len = int(str_len)
    str_itself = encoded_bytes[digits_in_str + 1: digits_in_str + 1 + str_len]
    return str_itself, digits_in_str + 1 + str_len

def decode_int(encoded_bytes):
    "i8e........"
    # we will find the first index of e
    index_of_e = encoded_bytes.find(b'e')
    return int(encoded_bytes[1:index_of_e]), index_of_e + 1

def decode_list(encoded_bytes):
    "li8e4:spame......."
    lis = []
    index = 1 # we know that index 0 is l, so starting from nex one
    while index < len(encoded_bytes):
        current_char = encoded_bytes[index]
        if current_char == ord(b'e'):
             # we finished iterating over the list, no point iterating over more
             # we will just update the index before
            index += 1
            break
        decoded_val, index_to_update = decode(encoded_bytes[index:])
        lis.append(decoded_val)
        index += index_to_update

    return lis, index

def decode_dict(encoded_bytes):
    "d3:key5value:li8e4:spame......."

    dic = dict()
    index = 1 # we know that index 0 is l, so starting from nex one
    while index < len(encoded_bytes):
        current_char = encoded_bytes[index]
        if current_char == ord(b'e'):
             # we finished iterating over the dict, no point iterating over more
             # we will just update the index before
            index += 1
            break
        decoded_val_as_key, index_to_update = decode(encoded_bytes[index:])
        index += index_to_update
        decoded_val_as_value, index_to_update = decode(encoded_bytes[index:])
        index += index_to_update
        dic[decoded_val_as_key] = decoded_val_as_value
    
    return dic,index

def decode(encoded_bytes):
    index = 0
    while index < len(encoded_bytes) and encoded_bytes[index] != ord(b'e'):
        current_char = encoded_bytes[index]

        if current_char == ord(b'i'):
            int_value, scanned_length = decode_int(encoded_bytes[index:])
            value = int_value
            index += scanned_length
            break
        elif current_char == ord(b'l'):
            lis_value, scanned_length = decode_list(encoded_bytes[index:])
            value = lis_value
            index += scanned_length
            break
        elif current_char == ord(b'd'):
            dic_value, scanned_length = decode_dict(encoded_bytes[index:])
            value = dic_value
            index += scanned_length
            break
        else:# default, meaning its string\bytes
            str_value, scanned_length = decode_str(encoded_bytes[index:])
            value = str_value
            index += scanned_length
            break
    
    return value, index
