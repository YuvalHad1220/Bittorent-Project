import string
def _decode(bencoded_bytes: bytes, decoded_dict: dict, start_search_index: int = 0):
    # we will find the first d, last e as they are the delimiters
    
    # dict start. we will verify dict end with an e
    if bencoded_bytes[start_search_index] == b'd':
        pass

    # integer start
    if bencoded_bytes[start_search_index] == b'i':
        pass
    
    if bencoded_bytes[start_search_index].isnumber
    #
def decode(bencoded_bytes):
    decoded_dict = dict()

    _decode(bencoded_bytes, decoded_dict)