import socket
import threading
from queue import Queue
import datetime
import sys
import json

sc = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
port = 2000
try:
    sc.bind(('',port))
except Exception as e:
    print(e)

print("Waiting for connections")
sc.listen()
byteLen = 90023

def recvMsg(leng,client):
    packet = client.recv(leng)
    if(packet ==''):
        return None
    if(len(packet)!=leng):
        #print(f"NOT THE RIGHT LENGTH")
        return packet +recvMsg(leng-len(packet),client)
    else:
        #print("Fixed length.")
        return packet

def clientThread(clnt,queue,inst):
    clnt.send(bytes("Connection Established.",'utf-8'))
    while True:
        if(not inst.empty()):
            clnt.send(bytes(inst.get(),'utf-8'))
            break
    
    for i in range(0,int(100000/10000)):
        message = recvMsg(byteLen,clnt)
        if not message:
            pass
            #clnt.sendall(("Connection was closed due to no data.").encode('utf-8'))
            #break
        if(len(message)!=byteLen):
           print(f"LOST DATA.{len(message)}")
           pass
        if(message.strip()!=''):
            queue.put(message)
    message = recvMsg(30,clnt)
    queue.put(message)
    clnt.close()
    totalThreads = threading.active_count() -1
    print(f"Total threads : {totalThreads}")
    sys.exit()

def printingThread(queue):
    data = [0,0]
    while True:
        if(not queue.empty()):
            current = queue.get()
            if(current != b''):
             
             try:
              jsonDat=json.loads(current.decode())
              current =jsonDat.get("data")
              index = jsonDat.get("info")[0]
              #index1 = current[0][0]
              
              if(current[0]=='END'):
                print(data[index])
                print(datetime.datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)"))
              else:
                dataPacket = current
                for value in dataPacket:
                    data[index] += int(value)
             
             except Exception as e:
                print(current)
                print(e)

totalConnections = 0
maxClients = 2


try:
 mainQ = Queue()
 instructionQueue= Queue()
 printer= threading.Thread(target=printingThread,args=(mainQ,))
 printer.start()
 threads = []
 while True:
    client,addr = sc.accept()
    print(f"Connection  has been made to {addr}!")
    totalConnections += 1
    if(totalConnections ==maxClients):
        now = datetime.datetime.now()
        startTime =now + datetime.timedelta(seconds=5)
        stringedTime = startTime.strftime("%d-%b-%Y (%H:%M:%S.%f)")
        print(startTime.strftime("%d-%b-%Y (%H:%M:%S.%f)"))
        for i in range(0,maxClients):
            instructionQueue.put(stringedTime)
    #print(instructionQueue)
    t= threading.Thread(target=clientThread,args=(client,mainQ,instructionQueue,))
    t.daemon = True
    t.start()

    totalThreads = threading.active_count()
    print(f"Total threads : {totalThreads}\n")
except (KeyboardInterrupt,SystemExit):
    sc.close()
    sys.exit()
except Exception as e:
    print(e)
sc.close()
        
