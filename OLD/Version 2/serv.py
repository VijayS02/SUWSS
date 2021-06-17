import socket
import time
import pickle
from queue import Queue
import threading
from datetime import datetime
import os

# NOTE THAT A POSSIBLE IMPLEMENTATION FOR SYNC IS TO ACCOUNT FOR PING
# SEND 5 MESSAGES FROM SERVER TO CLIENT AND GET AVERAGE PING.
# USE THIS PING TO TELL PROGRAM WHEN TO START.


LOCAL_PATH = 'store'
HEADERSIZE = 10


def send(msg_type, message, sock):
    request = {"type": msg_type, "content": message}
    msg = pickle.dumps(request)
    msg = bytes(f"{len(msg):<{HEADERSIZE}}", 'utf-8') + msg
    sock.send(msg)


def raw_recieve(sock):
    full_msg = b''
    header = -1
    while True:
        msg = sock.recv(32)
        if msg != b'':
            full_msg += msg
            header = int(full_msg[:HEADERSIZE])
            if len(full_msg[HEADERSIZE:]) == header:
                return full_msg[HEADERSIZE:]


def main_recieve(sock, addr):
    message = pickle.loads(raw_recieve(sock))
    if message['type'] == "pingtest":
        ping_test(message['content'], addr)
    elif message['type'] == "message":
        print(f"{addr}: {message['content']}")
    return message


def make_dir(direc):
    if not os.path.exists(direc):
        os.makedirs(direc)


def ping_test(server_time, addr):
    ping = (time.time() - server_time) * 1000
    print(f"{addr} Ping: %3d ms" % ping)


def manage_client(sock, addr, q, compq):
    try:

        print(f"{addr}: Connection from {addr} has been established. ")

        send("pingtest", time.time(), sock)

        main_recieve(sock, addr)

        while True:
            # Main program
            data = q.get()
            if data['time'] == -1:
                print("STOPPING THREAD")

                break
            iters = 10
            send("command", {"exec": "record", "channel_list": [0], "mode": "start", 'iters': iters,
                             'start_time': data['time'], 'sample_period': 20}, sock)

            ip_addr = addr[0].replace('.', '-') + "-" + str(addr[1])
            with open(f'{LOCAL_PATH}/{data["fold"]}/{ip_addr}.csv', 'a') as fd:
                inflow = main_recieve(sock, addr)
                count = 0
                while inflow['type'] != 'end':
                    if inflow['type'] == 'data':
                        for val in inflow['content'][0]:
                            fd.write(str(val) + "\n")
                        count += 1
                        print(count)
                    inflow = main_recieve(sock, addr)

            # Result
            print("Done")
            main_recieve(sock, addr)
            compq.put(1)
        compq.put(1)
        send("command", {"exec": "quit"}, sock)
        sock.close()


    except Exception as e:
        print(f"{addr}: Error, terminated connection.")
        sock.close()
        raise e


if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('192.168.0.103', 54555))
    s.listen(5)
    total_conns = 1
    threads = []
    queues = []
    try:
        while len(threads) < total_conns:
            clientsock, addr = s.accept()
            q = Queue()
            cq = Queue()
            t = threading.Thread(target=manage_client, args=(clientsock, addr, q, cq))
            t.daemon = True
            threads.append(t)
            queues.append([q, cq])
            print(f"{len(threads)}/{total_conns} connected.")
            t.start()

        time.sleep(1)
        # Main instructions
        while True:
            if input("Press enter to start...\n") == "-1":
                break
            rec = time.time() + 2
            folder = datetime.utcfromtimestamp(rec).strftime('%Y-%m-%d_%H-%M-%S')
            make_dir(LOCAL_PATH + "/" + folder)
            for ques in queues:
                ques[0].put({'cmd': "record", 'fold': folder, 'time': rec})

            # Check for completion
            sum_v = 0
            while sum_v < total_conns:
                for ques in queues:
                    sum_v += ques[1].get()

    except KeyboardInterrupt:
        for ques in queues:
            ques[0].put({'fold': '', 'time': -1})
        for thr in threads:
            thr.join()
        print("Closing... goodbye!")
