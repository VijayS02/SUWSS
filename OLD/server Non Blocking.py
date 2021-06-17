import socket
import threading
from queue import Queue

sc = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
port = 2000

def clientThread(clnt,queue,inst):
    clnt.send(bytes("Connection Established.",'utf-8'))
    while True:
        if(not inst.empty):
            clnt.send(bytes("start",'utf-8'))
    while True:
        message = clnt.recv(2048)
        queue.put(message.decode('utf-8'))
        if not message:
            clnt.sendall(("Connection was closed due to no data.").encode('utf-8'))
            break
    clnt.close()
    totalThreads = threading.active_count() -1
    print(f"Total threads : {totalThreads}")

def printingThread(queue):
    while True:
        if(not queue.empty()):
            print(queue.get())


            

try:
    sc.bind((socket.gethostname(),port))
except Exception as e:
    print(e)


sc.listen(100)



try:
 mainQ = Queue()
 instructionQueue= Queue()
 printer= threading.Thread(target=printingThread,args=(mainQ,))
 printer.start()
 while True:
    print("Waiting for connections")
    client,addr = sc.accept()
    print(f"Connection  has been made to {addr}!")
    t= threading.Thread(target=clientThread,args=(client,mainQ,instructionQueue,))
    t.start()
    totalThreads = threading.active_count()
    print(f"Total threads : {totalThreads}\n")
except (KeyboardInterrupt,SystemExit):
    cleanup_stop_thread()
    sc.close()
sc.close()
        
