import socket
import pickle
import time
HEADERSIZE = 10
from recordingPlain import main
from common_functions import send, raw_receive
from uploadWorker import Worker


def main_recieve(sock):
    message = raw_receive(sock)
    if message['type'] == "pingtest":
        send('pingtest', message['content'], sock)
        # ping_test(message['content'])
    elif message['type'] == "message":
        print(message['content'])
    return message


def ping_test(server_time):
    ping = (time.time() - server_time) * 1000
    print("Ping: %3d ms" % ping)


def commands(command_dat, sock):
    command_dat = command_dat['content']
    if command_dat['exec'] == 'record':
        sender = Worker(sock)
        curr = 0
        diff = command_dat['start_time'] - time.time()
        for item in main(command_dat):
            sender.upload(item)
        sender.stop()
        send("end", 0.0, sock)
        send("message", "Done.", s)
        print("Recording done, resetting loop")


if __name__ == "__main__":
    while True:
        try:
            s = None
            while True:
                waiting = False
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect(('192.168.1.222', 54555))
                    s.settimeout(10)
                    break
                except socket.timeout:
                    if not waiting:
                        waiting = True
                        print("waiting")
            s.settimeout(None)
            print("Connected.")
            main_recieve(s)
            send("pingtest", time.time(), s)
            while True:
                command = main_recieve(s)
                if command['type'] == 'command':
                    commands(command, s)
                    if command['content']['exec'] == 'quit':
                        break
        except Exception as e:
            print("Disconnected from server. Restarting..")
