"""
common_functions
"""
import pickle

HEADERSIZE = 10


def send(msg_type, message, sock):
    request = {"type": msg_type, "content": message}
    msg = pickle.dumps(request)
    msg = bytes(f"{len(msg):<{HEADERSIZE}}", 'utf-8') + msg
    sock.send(msg)


def raw_receive(sock):
    full_msg = b''
    while True:
        msg = sock.recv(32)
        if msg != b'':
            full_msg += msg
            header = int(full_msg[:HEADERSIZE])
            if len(full_msg[HEADERSIZE:]) == header:
                return pickle.loads(full_msg[HEADERSIZE:])
