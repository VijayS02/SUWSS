"""
Server functions that handle multiple client objects.

Copyright © Vijay Sambamurthy 2021.
Rights given to HKUST Civil Engineering Department.
"""
import os
import socket
import time
from datetime import datetime
import logging

from Client import Client
from graph import create_graph

LOCAL_PATH = 'store'
logger = logging.getLogger(__name__)


def make_dir(direc: str):
    """
    Make a directory at the given location if it does not already exist
    Args:
        direc: directory location
    """
    if not os.path.exists(direc):
        os.makedirs(direc)


def convert_to_channel_dict(channel_list: list, data: list) -> dict:
    """
    Convert data from the DAQ hat into a dictionary which maps each channel to its data.
    Args:
        channel_list: List of channels being used, e.g. [0,2,3,6]
        data: Raw data from DAQ hat

    Returns: Dictionary of data e.g. {0: [], 2: [], 3: [], 6: []}

    """
    res = {}
    num_channels = len(channel_list)
    for channel, count in zip(channel_list, range(num_channels)):
        res[channel] = data[count::num_channels]
    return res


def setup_connections(sock: socket.socket, conns: int) -> list[Client]:
    """
    Create Client objects for each accepted connection
    Args:
        sock: socket to accept connections from
        conns: total connections to accept

    Returns: list of client objects

    """
    logger.debug(f"Setting up connections with {conns} clients.")
    client_list = []
    while len(client_list) < conns:
        client_sock, address = sock.accept()
        cli = Client(client_sock, address)
        client_list.append(cli)
        logger.info(f"{len(client_list)}/{conns} connected.")
    return client_list


def record_clients(client_list: list[Client], sample_period: int, iters, offset=5) -> str:
    """
    Commands the client objects to begin recording.
    Args:
        client_list: list of clients that need to be recorded from
        sample_period: sample period in microseconds
        iters: iterations to record
        offset: seconds from now at which to begin

    Returns: folder at which recording data is being stored

    """
    rec = time.time() + offset
    folder = datetime.utcfromtimestamp(rec).strftime('%Y-%m-%d_%H-%M-%S')
    make_dir(LOCAL_PATH + "/" + folder)
    logger.debug(f"Recording to: '{folder}' folder.")
    for client_obj in client_list:
        client_obj.set_task({'command': "record", 'folder': folder, 'time': rec, 'iters': iters,
                             'sample_period': sample_period, 'channel_list': None})
    return folder


def get_client_results(client_list: list[Client]) -> dict:
    """
    Get the results of a recording/task from the client object.
    Args:
        client_list: List of client objects to check

    Returns: dictionary mapping the address of the client to its result.

    """
    completed = {}
    for client_obj in client_list:
        completed[client_obj.get_addr()] = client_obj.get_info()
    return completed


def wait_for_client_completion(client_list: list[Client]):
    """
    Wait for clients to complete current task. (i.e. until client status == "Idle")
    Args:
        client_list: list of clients to check.
    """
    while not (all([client.get_status() == "Idle" for client in client_list])):
        time.sleep(0.2)
    return


if __name__ == "__main__":
    SAMPLE_PERIOD = 10
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('192.168.1.222', 54555))
    s.listen(5)
    total_conns = 2
    clients = []
    ani = None
    try:
        clients = setup_connections(s, total_conns)
        time.sleep(1)

        while True:
            if input("Press enter to start...\n") == "-1":
                break
            record_clients(clients, SAMPLE_PERIOD, 10)
            ani = create_graph(clients, SAMPLE_PERIOD)

            # Check if all are success
            if not all([i['status'] == 'success' for i in get_client_results(clients).values()]):
                print("FAIL.")

    except KeyboardInterrupt:
        for client in clients:
            client.stop()
        while not (all([client.get_status() == "Dead" for client in clients])):
            print([client.get_status() for client in clients])
            time.sleep(1)
            exit()
