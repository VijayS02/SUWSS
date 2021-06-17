"""
Threading code for server

Copyright © Vijay Sambamurthy 2021.
Rights given to HKUST Civil Engineering Department.
"""
import threading
from queue import Queue
import socket

from Client import Client
from server import record_clients, setup_connections
from typing import Optional
import logging

logger = logging.getLogger(__name__)

IP = '192.168.1.222'


class ThreadWorker:
    """
    GUI helper thread to manage more computational tasks without locking the GUI.
    """
    _run_thread: threading.Thread
    _instruction_queue: Queue
    _output_queue: Queue
    _error_queue: Queue
    _kill_queue: Queue
    _clients: Optional[list[Client]]

    def __init__(self) -> None:
        logger.debug(f"Creating new gui thread worker. IP to connect {IP}")
        self._instruction_queue = Queue()
        self._output_queue = Queue()
        self._kill_queue = Queue()
        self._run_thread = threading.Thread(target=self.main)
        self._run_thread.start()
        self._error_queue = Queue()
        self._clients = None

    def stop(self, blocking: bool = False):
        """
        Stop the helper thread and cease execution.
        Args:
            blocking: whether the execution of this function should block other code from running.
        """
        logger.debug(f"Gui Thread worker being killed.")
        self._output_queue.put("Kill.")
        if blocking:
            self._run_thread.join()

    def get_clients(self) -> list[Client]:
        """
        Get the clients being worked on.
        Returns: list of clients

        """
        return self._clients

    def add_task(self, task: dict):
        """
        Add a task to execute.
        Args:
            task: task to complete
        """

        logger.debug(f"Task added to gui thread worker {task}")
        self._instruction_queue.put(task)

    def throw_error(self, error: any):
        """
        Throw errors without halting execution. ***NOT IMPLEMENTED FULLY***
        Args:
            error: Error to be thrown
        """
        print(error)
        logger.error(f"Error occurred in gui thread worker: {error}")
        self._error_queue.put(error)

    def connect(self, desired_clients: int, max_conns: int = 20):
        """
        Setup connections to all clients
        Args:
            desired_clients: Total clients that are desired to be connected to
            max_conns: Max connections that the socket should handle
        """
        if self._clients is not None:
            logger.debug("Clients already established, attempting to kill connections.")
            for client in self._clients:
                client.stop()

        logger.info("Listening for client connections.")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((IP, 54555))
        s.listen(max_conns)
        self._clients = setup_connections(s, desired_clients)

    def record(self, sampls: int, iters: int, starting_offset: int = 5):
        """
        Execute record command
        """
        if self._clients is not None:
            record_clients(self._clients, sampls, iters, offset=starting_offset)
        else:
            self.throw_error("Please setup client connection first.")

    def main(self) -> None:
        """
        Main execution for the thread.
        """
        while self._kill_queue.empty():
            task = self._instruction_queue.get()
            if task['func'] == 'Connect':
                self.connect(task['desired_clients'], task['max_conns'])
            elif task['func'] == 'Record':
                self.record(task['sampls'], task['iters'], task['start_offset'])
