# example of queue operations in the torrent handler
import asyncio


# that db queue basically just updates the db. we use a set because in the end, we are saving the torrent files and we dont want duplications
class DBQueue:
    def __init__(self) -> None:
        self.queue = set()
        self.torrent_db = None

    def add_torrent_to_queue(self):
        pass

    async def update_db_loop(self):
        while True:
            task = await self.queue.get()