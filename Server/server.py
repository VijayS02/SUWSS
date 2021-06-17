"""
Server.py

This file is Copyright (c) 2021 Vijay Sambamurthy.
"""
import os
import socket
import time
from datetime import datetime

from Client import Client
from graph import create_graph
LOCAL_PATH = 'store'


def make_dir(direc):
    if not os.path.exists(direc):
        os.makedirs(direc)


def convert_to_channel_dict(channel_list, data):
    res = {}
    num_channels = len(channel_list)
    for channel, count in zip(channel_list, range(num_channels)):
        res[channel] = data[count::num_channels]
    return res


def setup_connections(sock, conns):
    client_list = []
    while len(client_list) < conns:
        client_sock, address = sock.accept()
        cli = Client(client_sock, address)
        client_list.append(cli)
        print(f"{len(client_list)}/{conns} connected.")
    return client_list


def record_clients(client_list, sample_period: int, iters, offset=5) -> str:
    rec = time.time() + offset
    folder = datetime.utcfromtimestamp(rec).strftime('%Y-%m-%d_%H-%M-%S')
    make_dir(LOCAL_PATH + "/" + folder)
    for client_obj in client_list:
        client_obj.set_task({'command': "record", 'folder': folder, 'time': rec, 'iters': iters,
                             'sample_period': sample_period, 'channel_list': None})
    return folder


def get_client_results(client_list):
    completed = {}
    for client_obj in client_list:
        completed[client_obj.get_addr()] = client_obj.get_info()
    return completed


def wait_for_client_completion(client_list):
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
