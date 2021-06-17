"""
Client file to manage client connections

Copyright © Vijay Sambamurthy 2021.
Rights given to HKUST Civil Engineering Department.
"""


import time
from queue import Queue
import threading
import socket
import logging
from common_functions import raw_receive, send

logger = logging.getLogger(__name__)

LOCAL_PATH = 'store'


class Client:
    """
    Client object type. Automatically creates a new thread and this object is used to manage
    the operation of the thread.
    """
    _sock: socket.socket
    _addr: tuple
    _instruction_queue: Queue
    graph_queue: Queue
    _information_queue: Queue
    _current_mode: str
    _runtime_thread: threading.Thread

    def __init__(self, client_socket: socket.socket, address: tuple):
        logger.debug(f"Initializing new client with address {address}.")
        self._current_mode = "Innit"
        self._sock = client_socket
        self._addr = address
        self._information_queue = Queue()
        self._instruction_queue = Queue()
        self.graph_queue = Queue()
        self._runtime_thread = threading.Thread(target=self.run_client, args=())
        self._runtime_thread.start()
        self._current_mode = "Idle"
        logger.debug(f"Client creation complete. {address}.")

    def run_client(self) -> None:
        """
        Main method of the client object. This runs a loop which executes commands and tasks
        set by the other programs.
        """
        logger.debug(f"New thread has been created.")

        logger.debug(f"Sending Ping Test to client.")
        send("pingtest", time.time(), self._sock)
        inflow = self.clean_receive()
        self.ping_test(inflow['content'])

        logger.debug(f"Waiting for task.")
        task = self._instruction_queue.get()
        while task != "terminate":
            if task['command'] == "record":
                try:
                    logger.debug(f"Recording, task: \n{task}")
                    self.record(task['time'], task['iters'], task['folder'], task['sample_period'],
                                task['channel_list'])
                except KeyError:
                    logger.exception(f"{self._addr}: Missing Required parameters for recording.")

            self._current_mode = "Idle"
            task = self._instruction_queue.get()

        logger.debug(f"Ending thread loop.")
        self._sock.shutdown(1)
        self._sock.close()
        logger.debug(f"{self._addr}: run_client loop exited. Thread exiting.")
        self._current_mode = "Dead"

    def __repr__(self) -> str:
        return "<Client Object Address:" + repr(self._addr) + \
               "  Current Mode:" + self._current_mode + ">"

    def set_task(self, task: object) -> None:
        """
        Sets a task for the run_thread method of this class. Sends the task to the other thread.
        Args:
            task: the task to be completed
        """
        if self._current_mode == "Dead":
            return
        self._instruction_queue.put(task)

    def get_info(self, block: bool = True) -> object:
        """
        Get any information from the operational thread worker.
        Returns: Any information from the queue
        """
        return self._information_queue.get(block=block)

    def get_addr(self) -> tuple:
        """
        Get the address of this instance of client.
        Returns: IP address tuple
        """
        return self._addr

    def get_status(self) -> str:
        """
        Get the current status of the worker thread.
        Returns: Either "Idle", "Recording" or "Dead"
        """
        return self._current_mode

    def ping_test(self, conn_time: time.time):
        """
        Conducts a ping test from the server.
        Args:
            conn_time: UNIX timestamp from time module that was initially sent to the client.

        Returns: Ping between server and client in ms.

        """
        ping = ((time.time() - conn_time) / 2) * 1000
        send("message", f"Ping: {ping}", self._sock)
        logger.debug(f"Ping is {ping} ms.")
        return ping

    def clean_receive(self) -> dict:
        """
        A function layered on top of the receive function from common_function. This allows messages
        to be directly printed and add functionality.

        Returns: the message dictionary (key-value pair)
        """
        message = raw_receive(self._sock)
        logger.debug("New Message.")
        if message['type'] == 'message':
            print(f"{self._addr} : {message['content']}")
            logger.info(f"{self._addr} : {message['content']}")
            return message
        else:
            return message

    def record(self, time_stamp: time.time, iters: int,
               folder: str, sample_period: int, channel_list: list = None) -> None:
        """
        Conduct a recording. This function sends a signal to the client to begin recording, and then
        it stores the stream of data from the socket into a csv file.
        Args:
            time_stamp: When to start recording.
            iters: number of iterations to record for (1 it = 1s)
            folder: Folder to store recordings into
            sample_period: the sample period in microseconds to record at
            channel_list: a list of the channels being used (*DO NOT USE) [REQUIRES FURTHER IMPL]
        """
        prev_mode = self._current_mode
        self._current_mode = "Recording"

        if channel_list is None:
            channel_list = [0]

        logger.debug("Sending record command to client.")
        # Send record command to client
        send("command", {"exec": "record",
                         "channel_list": channel_list,
                         'iters': iters,
                         'start_time': time_stamp,
                         'sample_period': sample_period}, self._sock)
        logger.debug(f"Thread Current mode: {self._current_mode}")

        # Setup folder and file to store data in
        ip_addr = self._addr[0].replace('.', '-') + "-" + str(self._addr[1])

        # Use context manager to open file
        with open(f'{LOCAL_PATH}/{folder}/{ip_addr}.csv', 'a+') as fd:

            # Get data from client
            inflow = self.clean_receive()
            count = 0
            while inflow['type'] != 'end':
                logger.debug(f"Data Inflow. Count: {count}")
                if inflow['type'] == 'data':
                    self.graph_queue.put(inflow['content'])
                    for val in inflow['content']:
                        fd.write(str(val) + "\n")
                    count += 1
                inflow = self.clean_receive()

        logger.debug(f"Recording done.")
        # Complete program
        self.clean_receive()
        self._information_queue.put({"status": "success",
                                     "file": f"{LOCAL_PATH}/{folder}/{ip_addr}.csv"})
        self._current_mode = prev_mode

    def stop(self, block: bool = False) -> None:
        """
        Stop the worker thread by sending kill command to the queue.
        """
        logger.debug(f"Stopping Thread.")
        self._instruction_queue.put("terminate")
        if block:
            self._runtime_thread.join()
