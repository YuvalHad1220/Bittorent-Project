from threading import Thread
import asyncio


class ThreadHandler:
    def __init__(self, app_thread, io_thread, announce_handler_loop, tcp_thread, udp_thread) -> None:
        self.app_thread: Thread = app_thread
        self.io_thread: Thread = io_thread
        self.announcement_loop = announce_handler_loop
        self.udp_thread = udp_thread
        self.tcp_thread = tcp_thread

    def start_threads(self):
        Thread(target=self._announcement_thread_start).start()

    def _announcement_thread_start(self):
        asyncio.run(self.announcement_loop)
