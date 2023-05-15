from torrent import Torrent
import pathlib
import hashlib
import encryption
from utils import torrent_types

class PieceHandler:

    def __init__(self, torrent: Torrent) -> None:
        self.torrent = torrent
        self.save_path = pathlib.Path(torrent.download_path) / f"{self.torrent.index}Pieces"
        self.save_path.mkdir(exist_ok=True)
        self.downloaded_pieces = bytearray([0]) * len(self.torrent.pieces_hashes_list)
        self.get_existing_pieces()

    
    @property
    def downloading(self):
        return True if self.torrent.downloaded < self.torrent.size else False

    def get_existing_pieces(self):
        for filename in self.save_path.glob('*'):
            index, _ = filename.name.split('.')
            self.downloaded_pieces[int(index)] = 1

    def on_validated_piece(self, validated_piece, piece_index):
        """
        That function will save the validated piece into memory. once we have all validated pieces only then we will construct files from them
        """

        with open(self.save_path / f"{self.needed_piece_to_download_index()}.piece", 'wb') as f:
            f.write(validated_piece)
            self.downloaded_pieces[piece_index] = 1


        self.torrent.downloaded += self.torrent.piece_size_in_bytes

        if self.torrent.downloaded >= self.torrent.size():
            self.on_download_finish()


    @property
    def needed_piece_to_download_index(self):
        for i, piece_downloaded_value in enumerate(self.downloaded_pieces):
            if piece_downloaded_value == 0:
                return i

        return -1

    def validate_piece(self, piece):
        """
        We will validate the piece against the current index
        """

        for i, piece_hash in enumerate(self.torrent.pieces_hashes_list):
            sha1 = hashlib.sha1()
            sha1.update(piece)
            res = sha1.digest()
            if res == piece_hash:
                print("PIECE EXISTS IN HASH LIST!! GOOD JOB ON GETTING THAT. PIECE INDEX:", i)
                return True

        print("piece does not exist")
        return False

    def on_download_finish(self):
        print("finished downloading")
        self.files_from_pieces()
        self.torrent.connection_info.state = torrent_types.wait_to_finish


    def files_from_pieces(self):
        for file_obj in self.torrent.files:
            file_path = pathlib.Path(self.save_path).parent / file_obj.path_name
            # file_path.mkdir(exist_ok=True)
            with open(file_path, 'wb') as f:
                for i in range(file_obj.first_piece_index, file_obj.last_piece_index):
                    with open(self.save_path / (str(i) + '.piece'), 'rb') as piece_file:
                        f.write(piece_file.read())

    def return_block(self, piece_index, block_offset, block_length, public_key=None):
        with open(self.torrent.download_path, 'rb') as f:
            byte_pos = piece_index * self.torrent.piece_size_in_bytes + block_offset
            f.seek(byte_pos)
            # Read the requested block
            block_data = f.read(block_length)

        if not public_key:
            return block_data

        return encryption.encrypt_using_public(block_data, public_key)
    
    