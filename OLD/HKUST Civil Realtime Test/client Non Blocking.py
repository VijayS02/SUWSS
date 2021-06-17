import socket
import random
import time


s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect(("localhost",2000))
sum1 = 0

while True:
     s.send(bytes("1 Sup","utf-8"))
     time.sleep(1)
