import socket
import random
import time
import datetime
import pause
import json

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("localhost", 2000))
sum1 = 0
client = 1

msg = s.recv(1024)
print(msg.decode('utf-8'))

msg = s.recv(1024)
print(msg.decode('utf-8'))
dt = datetime.datetime.strptime(msg.decode('utf-8'), "%d-%b-%Y (%H:%M:%S.%f)")
pause.until(dt)
userData = [client]
length = 0
store = []
sendVal = ''
for i in range(0, 100000):
    x = random.randint(0, i)

    store.append((format(x, '05')))
    sum1 += int(x)
    if (i + 1) % 10000 == 0:
        send = json.dumps({"info": userData, "data": store})
        sendVal = send.encode()
        s.send(sendVal)
        store = []

print(len(json.dumps({"info": userData, "data": ["END"]}).encode()))
s.send(json.dumps({"info": userData, "data": ["END"]}).encode())
s.close()
print("The sum should be: ", sum1)
print(datetime.datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)"))
