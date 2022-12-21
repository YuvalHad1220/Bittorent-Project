"https://shekhargulati.com/2020/09/19/writing-bencode-parser-in-kotlin/"

def encode(item):
    if isinstance(item, str):
        return f"{len(item)}:{item}"

    if isinstance(item, int):
        return f"i{item}e"

    if isinstance(item, list):
        # for every item in list we need to encode
        st = "l"
        st+= ''.join([encode(item_in_list) for item_in_list in item])
        st+= "e"
        return st
    
    if isinstance(item, dict):
        st = "d"
        st+= ''.join([encode(key)+encode(value) for key,value in item.items()])
        st += "e"
        return st


def decode_str(encoded_str):
    "4:spam........."
    str_len = encoded_str.split(':')[0]
    digits_in_str = len(str_len)
    str_len = int(str_len)
    str_itself = encoded_str[digits_in_str + 1: digits_in_str + 1 + str_len]
    return str_itself, digits_in_str + 1 + str_len

def decode_int(encoded_str):
    "i8e........"
    # we will find the first index of e
    index_of_e = encoded_str.find('e')
    return int(encoded_str[1:index_of_e]), index_of_e + 1

def decode_list(encoded_str):
    "li8e4:spame......."
    lis = []
    index = 1 # we know that index 0 is l, so starting from nex one
    while index < len(encoded_str):
        current_char = encoded_str[index]
        if current_char == 'e':
             # we finished iterating over the list, no point iterating over more
             # we will just update the index before
            index += 1
            break
        decoded_val, index_to_update = decode(encoded_str[index:])
        lis.append(decoded_val)
        index += index_to_update

    return lis, index

def decode_dict(encoded_str):
    "d3:key5value:li8e4:spame......."

    dic = dict()
    index = 1 # we know that index 0 is l, so starting from nex one
    while index < len(encoded_str):
        current_char = encoded_str[index]
        if current_char == 'e':
             # we finished iterating over the dict, no point iterating over more
             # we will just update the index before
            index += 1
            break
        decoded_val_as_key, index_to_update = decode(encoded_str[index:])
        index += index_to_update
        decoded_val_as_value, index_to_update = decode(encoded_str[index:])
        index += index_to_update
        dic[decoded_val_as_key] = decoded_val_as_value
    
    return dic,index

def decode(encoded_str):
    index = 0
    while index < len(encoded_str) and encoded_str[index] != 'e':
        current_char = encoded_str[index]
        match current_char:
            case 'i':
                int_value, scanned_length = decode_int(encoded_str[index:])
                value = int_value
                index += scanned_length
                break
            case 'l':
                lis_value, scanned_length = decode_list(encoded_str[index:])
                value = lis_value
                index += scanned_length

            case 'd':
                dic_value, scanned_length = decode_dict(encoded_str[index:])
                value = dic_value
                index += scanned_length
                break

            case _: # default, meaning its string
                str_value, scanned_length = decode_str(encoded_str[index:])
                value = str_value
                index += scanned_length
                break
        
    return value, index
