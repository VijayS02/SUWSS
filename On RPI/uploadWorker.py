import threading
from queue import Queue
from common_functions import send
import socket


class Worker():
    _run_thread: threading.Thread
    _uploading_info: Queue
    _sock: socket.socket
    _information_info: Queue

    def __init__(self, s: socket.socket):
        self._uploading_info = Queue()
        self._sock = s
        self._information_info = Queue()
        self._run_thread = threading.Thread(target=self.runner)
        self._run_thread.start()

    def upload(self, items: any):
        self._uploading_info.put(items)

    def stop(self):
        self._information_info.put("Kill")
        self._run_thread.join()

    def runner(self):
        while True:
            if not self._information_info.empty():
                break
            if not self._uploading_info.empty():
                send("data", self._uploading_info.get_nowait(), self._sock)
