from threading import Thread
import asyncio
class ThreadHandler:
    def __init__(self, app_thread, announcement_main_loop: asyncio.Task) -> None:
        self.app_thread: Thread = app_thread
        self.io_thread: Thread = None
        self.announcement_task = announcement_main_loop
        self.announcement_thread = announcement_main_loop
        self.peer_threads = []


    def start_threads(self):
        self.announcement_thread = Thread(target= self._announcement_thread_start)
        self.announcement_thread.start()

    def _announcement_thread_start(self):
        asyncio.run(self.announcement_task)