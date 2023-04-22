from torrent import Torrent
import pathlib
import hashlib


class PieceHandler:

    def __init__(self, torrent: Torrent) -> None:
        self.torrent = torrent
        self.save_path = torrent.download_path
        self.downloaded_pieces = -1
        self.get_existing_pieces()

    def get_existing_pieces(self):
        path = pathlib.Path(self.save_path)
        pieces_path = path / "pieces"
        pieces_path.mkdir(exist_ok=True)
        pieces_count = len(list(pieces_path.glob('*')))
        self.downloaded_pieces = pieces_count
        print(self.downloaded_pieces)

    def on_validated_piece(self, validated_piece):
        """
        That function will save the validated piece into memory. once we have all validated pieces only then we will construct files from them
        """
        path = pathlib.Path(self.save_path)
        pieces_path = path / "pieces"
        print(pieces_path.absolute())
        with open(pieces_path / f"{self.downloaded_pieces}.piece",'wb') as f:
            f.write(validated_piece)

            self.downloaded_pieces += 1

    def needed_piece_to_download_index(self):
        if len(self.torrent.pieces_info.pieces_hashes_list) < self.downloaded_pieces:
            return -1
        
        return self.downloaded_pieces
    
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
        """
        Once we have all pieces we need to construct the file.

        """
        pass