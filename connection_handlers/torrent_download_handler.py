from torrent import Torrent

BLOCK_SIZE = 4096

"""
LOGIC: We will try to download from each peer a random block; we will try to 

"""


class DownloadHandler:
    def __init__(self, torrent: Torrent, connected_peers) -> None:
        self.torrent = torrent
        self.connected_peers = connected_peers

    def run(self):
        piece_size = self.torrent.pieces_info.piece_size_in_bytes
        pieces_amount = len(self.torrent.pieces_info.pieces_hashes_list)

        for file in self.torrent.files:
            file_name = file.path_name
            piece_index = file.first_piece_index
            last_piece_index = file.last_piece_index

            # downloading every piece for file
            while piece_index < last_piece_index:
                if not torrenthandler.is_piece_need_to_download(torrent, piece_index):
                    continue


                if bytes_downloaded_so_far +block_length>file_size:
                    block_size = remainder of file

                # we will ask for each peer a random block in piece so we could gather all of that block in an instant
                first_task = create_task(piece_index, start_block, start_block+i)
                second_task = create_tasl(piece_index, start_block+i+1, start_block + 1 + 2*i)

                # once completed
                if piece_validated:
                    save_to_file(piece)
                    torrent_handler.remove_piece_from_list(torrent, piece_index)








            bytes_to_download = file.size_in_bytes



            piece_index = pieces_downloaded_global
            # this will be the download part
            while bytes_downloaded < bytes_to_download:
                block = connected_peer.download_block()















                for piece in pieces:
                    for peer in peers:
                        # run download task
                        break # when a piece is downloaded

                    if piece.isgood:
                        add_to_file(filename, piece)
                        pieces.pop(piece)
                    else:
                        pieces.append(piece)