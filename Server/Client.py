import time
from queue import Queue
import threading
import socket
from common_functions import raw_receive, send

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

    def __init__(self, client_socket, address):
        self._current_mode = "Innit"
        self._sock = client_socket
        self._addr = address
        self._information_queue = Queue()
        self._instruction_queue = Queue()
        self.graph_queue = Queue()
        self._runtime_thread = threading.Thread(target=self.run_client, args=())
        self._runtime_thread.start()
        self._current_mode = "Idle"

    def run_client(self) -> None:
        send("pingtest", time.time(), self._sock)
        print("Sent Pingtest")
        inflow = self.clean_receive(self._sock)
        self.ping_test(inflow['content'])

        task = self._instruction_queue.get()
        while task != "terminate":
            if task['command'] == "record":
                try:
                    self.record(task['time'], task['iters'], task['folder'], task['sample_period'],
                                task['channel_list'])
                except KeyError as err:
                    print(f"{self._addr}: Missing Required parameters for recording.")
                    print("\t", err)

            self._current_mode = "Idle"
            task = self._instruction_queue.get()

        self._sock.shutdown(1)
        self._sock.close()
        print(f"{self._addr}: run_client loop exited. Thread exiting.")
        self._current_mode = "Dead"

    def __repr__(self) -> str:
        return "<Client Object Address:" + repr(self._addr) + \
               "  Current Mode:" + self._current_mode + ">"

    def set_task(self, task: object) -> None:
        if self._current_mode == "Dead":
            return
        self._instruction_queue.put(task)

    def get_info(self, block: bool = True) -> object:
        return self._information_queue.get(block=block)

    def get_addr(self):
        return self._addr

    def get_status(self) -> str:
        return self._current_mode

    def ping_test(self, conn_time):
        ping = ((time.time() - conn_time) / 2) * 1000
        print("Ping: %3d ms" % ping)
        send("message", f"Ping: {ping}", self._sock)
        return ping

    def clean_receive(self, sock):
        message = raw_receive(sock)
        if message['type'] == 'message':
            print(f"{self._addr} : {message['content']}")
            return message
        else:
            return message

    def record(self, time_stamp: time.time, iters: int,
               folder: str, sample_period: int, channel_list: list = None) -> None:
        prev_mode = self._current_mode
        self._current_mode = "Recording"

        if channel_list is None:
            channel_list = [0]

        # Send record command to client
        send("command", {"exec": "record",
                         "channel_list": channel_list,
                         'iters': iters,
                         'start_time': time_stamp,
                         'sample_period': sample_period}, self._sock)
        print(self._current_mode)
        # Setup folder and file to store data in
        ip_addr = self._addr[0].replace('.', '-') + "-" + str(self._addr[1])

        # Use context manager to open file
        with open(f'{LOCAL_PATH}/{folder}/{ip_addr}.csv', 'a+') as fd:

            # Get data from client
            inflow = self.clean_receive(self._sock)
            count = 0
            while inflow['type'] != 'end':
                if inflow['type'] == 'data':
                    self.graph_queue.put(inflow['content'])
                    for val in inflow['content']:
                        fd.write(str(val) + "\n")
                    count += 1
                inflow = self.clean_receive(self._sock)

        # Complete program
        self.clean_receive(self._sock)
        self._information_queue.put({"status": "success",
                                     "file": f"{LOCAL_PATH}/{folder}/{ip_addr}.csv"})
        self._current_mode = prev_mode

    def stop(self, block: bool = False) -> None:
        self._instruction_queue.put("terminate")
        if block:
            self._runtime_thread.join()
