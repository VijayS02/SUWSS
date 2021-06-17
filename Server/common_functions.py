"""
Common functions to be used accross server and client

Copyright © Vijay Sambamurthy 2021.
Rights given to HKUST Civil Engineering Department.
"""
import logging
import pickle
import socket
import time

logger = logging.getLogger(__name__)

HEADERSIZE = 20


def time_wrapper(func, *args):
    """
    Decorator for function to add time delay if necessary. *This is used for sockets to allow
    the packets to flow without flooding the connection.
    """
    def wrapper():
        time.sleep(0.1)
        func(*args)
        time.sleep(0.1)
    return wrapper

@time_wrapper
def send(msg_type: str, message: any, sock: socket.socket):
    """
    Send a message through the given socket.
    Args:
        msg_type: The type of message that would like to be sent (can be anything e.g. "data",
        "message", "end") Just metadata.
        message: Message content that will be put under the "content" key
        sock: socket to send message via.
    """
    logger.debug(f"Call to send, sending message...Headersize: {HEADERSIZE}")
    request = {"type": msg_type, "content": message}
    msg = pickle.dumps(request)
    msg = bytes(f"{len(msg):<{HEADERSIZE}}", 'utf-8') + msg
    sock.send(msg)
    logger.debug("Message sent.")


def raw_receive(sock: socket.socket):
    """
    Receive message from the given socket
    Args:
        sock: the socket from which to receive message from.

    Uses HEADERSIZE to define message length.  (Please make sure this is the same across devices)
    Returns: The full message loaded from pickle.

    """
    full_msg = b''
    while True:
        msg = sock.recv(2**12)
        if msg != b'':
            full_msg += msg
            header = int(full_msg[:HEADERSIZE])
            if len(full_msg[HEADERSIZE:]) == header:
                return pickle.loads(full_msg[HEADERSIZE:])
