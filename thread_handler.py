import threading
import psutil

class customThread(threading.Thread):
    def __init__(self, name, *args, **kwargs):
        self.name = name
        super().__init__(*args, **kwargs)

    def load_per_thread(self):
        process = psutil.Process()
        num_cores = psutil.cpu_count()
        for thread in process.threads():
            if thread.id == self.ident:
                thread_info = thread.info
                user_time = thread_info.user_time
                system_time = thread_info.system_time
                total_time = user_time + system_time
                cpu_percent = (total_time / num_cores) * 100
                return cpu_percent


class threadHandler:
    def __init__(self) -> None:
        self.app_thread = None
        self.io_thread = None
        self.announcement_thread = None
        self.peer_threads = []


    def as_dict(self):
        # as for peer thread, we will retrieve its id by the index in the list.
        data = {
            "app_thread": {"load_per_thread": self.app_thread.load_per_thread()},
            "io_thread": {"load_per_thread": self.io_thread.load_per_thread()},
            "announcement_thread": {"load_per_thread": self.announcement_thread.load_per_thread()},
            "peer_threads": [
                {"load_per_thread": peer_thread.load_per_thread()} for peer_thread in self.peer_threads
            ],
        }
        return data
