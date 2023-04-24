from torrent import Torrent
import pathlib
import hashlib
import os

class PieceHandler:

    def __init__(self, torrent: Torrent) -> None:
        self.torrent = torrent
        self.save_path = torrent.download_path
        self.downloaded_pieces = bytearray([0]) * len(self.torrent.pieces_info.pieces_hashes_list)

    def get_existing_pieces(self):
        path = pathlib.Path(self.save_path)
        pieces_path = path / "pieces"
        pieces_path.mkdir(exist_ok=True)
        for filename in pieces_path.glob('*'):
            index, _ = filename.name.split('.')
            self.downloaded_pieces[int(index)] = 1

    def on_validated_piece(self, validated_piece, piece_index):
        """
        That function will save the validated piece into memory. once we have all validated pieces only then we will construct files from them
        """
        path = pathlib.Path(self.save_path)
        pieces_path = path / "pieces"
        with open(pieces_path / f"{self.downloaded_pieces}.piece",'wb') as f:
            f.write(validated_piece)

            self.downloaded_pieces[piece_index] = 1

    def needed_piece_to_download_index(self):
        for i, piece_downloaded_value in enumerate(self.downloaded_pieces):
            if piece_downloaded_value == 0:
                return i 
            

        return -1
    
    def validate_piece(self, piece):
        """
        We will validate the piece against the current index
        """

        with open('current_piece', 'wb') as f:
            f.write(piece)

        for piece_hash in self.torrent.pieces_info.pieces_hashes_list:
            # piece_hash = self.torrent.pieces_info.pieces_hashes_list[self.downloaded_pieces]
            sha1 = hashlib.sha1()
            sha1.update(piece)
            res = sha1.digest()
            if res == piece_hash:
                print("equals")
                return True

        return False

        print(self.downloaded_pieces)
        print(res)
        print(piece_hash)
        return res == piece_hash
    
    def on_download_finish(self):
        self.multiple_files_from_pieces()
        # extra things to do if needed

    def multiple_files_from_pieces(self):
        for file_obj in self.torrent.files:
            file_path = pathlib.Path(self.save_path) / file_obj.path_name
            file_path.mkdir(exist_ok=True)
            with open(file_path, 'wb') as f:
                for i in range(file_obj.first_piece_index, file_obj.last_piece_index+1):
                    piece_path = os.path.join(self.torrent.file_path, str(i) + '.piece')
                    with open(piece_path, 'rb') as piece_file:
                        f.write(piece_file.read())


    def return_block(self, piece_index, block_offset, block_length):
        with open(self.torrent.download_path, 'rb') as f:
            byte_pos = piece_index * self.torrent.pieces_info.piece_size_in_bytes + block_offset
            f.seek(byte_pos)
            # Read the requested block
            block_data = f.read(block_length)

        return block_data