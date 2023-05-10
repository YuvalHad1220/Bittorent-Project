from torrent import Torrent
import pathlib
import hashlib
import encryption


class PieceHandler:

    def __init__(self, torrent: Torrent) -> None:
        self.torrent = torrent
        self.save_path = pathlib.Path(torrent.download_path) / "Pieces"
        self.downloaded_pieces = bytearray([0]) * len(self.torrent.pieces_info.pieces_hashes_list)
        self.downloading = True
        self.uploading = False
        self.get_existing_pieces()

    def get_existing_pieces(self):
        self.save_path.mkdir(exist_ok=True)
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

        if self.needed_piece_to_download_index() == -1:
            self.downloading = False

        self.torrent.downloaded += self.torrent.pieces_info.piece_size_in_bytes

    def needed_piece_to_download_index(self):
        for i, piece_downloaded_value in enumerate(self.downloaded_pieces):
            if piece_downloaded_value == 0:
                return i

        return -1

    def validate_piece(self, piece):
        """
        We will validate the piece against the current index
        """

        for i, piece_hash in enumerate(self.torrent.pieces_info.pieces_hashes_list):
            sha1 = hashlib.sha1()
            sha1.update(piece)
            res = sha1.digest()
            if res == piece_hash:
                print("PIECE EXISTS IN HASH LIST!! GOOD JOB ON GETTING THAT. PIECE INDEX:", i)
                return True

        print("piece does not exist")
        return False

    def on_download_finish(self):
        self.multiple_files_from_pieces()
        # extra things to do if needed

    def multiple_files_from_pieces(self):
        for file_obj in self.torrent.files:
            file_path = pathlib.Path(self.save_path).parent / file_obj.path_name
            # file_path.mkdir(exist_ok=True)
            with open(file_path, 'wb') as f:
                for i in range(file_obj.first_piece_index, file_obj.last_piece_index):
                    with open(self.save_path / (str(i) + '.piece'), 'rb') as piece_file:
                        f.write(piece_file.read())

    def return_block(self, piece_index, block_offset, block_length, public_key=None):
        with open(self.torrent.download_path, 'rb') as f:
            byte_pos = piece_index * self.torrent.pieces_info.piece_size_in_bytes + block_offset
            f.seek(byte_pos)
            # Read the requested block
            block_data = f.read(block_length)

        if not public_key:
            return block_data

        return encryption.encrypt_using_public(block_data, public_key)

    def is_downloaded(self):
        return self.get_existing_pieces() == -1
