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
        pieces_count = len(list(path.glob('*')))
        self.downloaded_pieces = pieces_count

    def on_validated_piece(self, validated_piece):
        """
        That function will save the validated piece into memory. once we have all validated pieces only then we will construct files from them
        """
        with open(self.downloaded_pieces + '.piece','wb') as f:
            f.write(validated_piece)

            self.downloaded_pieces += 1

    def needed_piece_to_download_index(self):
        if len(self.torrent.pieces_info.pieces_hashes_list) < self.downloaded_pieces:
            return self.downloaded_pieces
        
        return -1
    
    def validate_piece(self, piece):
        """
        We will validate the piece against the current index
        """

        piece_hash = self.torrent.pieces_info.pieces_hashes_list[self.downloaded_pieces]
        sha1 = hashlib.sha1()
        sha1.update(piece)
        return sha1.digest() == piece_hash
    

    def on_download_finish(self):
        """
        Once we have all pieces we need to construct the file.

        """
        pass