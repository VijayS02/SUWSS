import threading
from queue import Queue
import socket

from Client import Client
from server import record_clients, setup_connections
from typing import Optional

IP = '192.168.1.222'


class thread_worker():
    _run_thread: threading.Thread
    _instruction_queue: Queue
    _output_queue: Queue
    _error_queue: Queue
    _kill_queue: Queue
    _clients: Optional[list[Client]]

    def __init__(self):
        self._instruction_queue = Queue()
        self._output_queue = Queue()
        self._kill_queue = Queue()
        self._run_thread = threading.Thread(target=self.main)
        self._run_thread.start()
        self._error_queue = Queue()
        self._clients = None

    def stop(self, blocking=False):
        self._output_queue.put("Kill.")
        if blocking:
            self._run_thread.join()

    def get_clients(self):
        return self._clients

    def add_task(self, task):
        self._instruction_queue.put(task)

    def throw_error(self, error):
        print(error)
        self._error_queue.put(error)

    def connect(self, desired_clients, max_conns=20):
        if self._clients is not None:
            for client in self._clients:
                client.stop()

        print("Listening...")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((IP, 54555))
        s.listen(max_conns)
        self._clients = setup_connections(s, desired_clients)

    def record(self, sampls, iters, starting_offset=5):
        if self._clients is not None:
            record_clients(self._clients, sampls, iters, offset=starting_offset)
        else:
            self.throw_error("Please setup client connection first.")

    def main(self):
        while self._kill_queue.empty():
            task = self._instruction_queue.get()
            if task['func'] == 'Connect':
                self.connect(task['desired_clients'], task['max_conns'])
            elif task['func'] == 'Record':
                self.record(task['sampls'], task['iters'], task['start_offset'])
