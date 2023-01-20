import threading
import psutil

class ExtendedThread(threading.Thread):
    def __init__(self, *args, **kwargs):
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