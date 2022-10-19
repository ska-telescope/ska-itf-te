#!/usr/bin/env python3

import socket
import time

# -------------------------- CONNECTION SETTINGS -------------------------------------------
ATT_HOST = '10.20.7.6'         # MS2090A spectrum analyzer IP
ATT_PORT = 23                # MS2090A spectrum analyzer port
ATT_ADDRESS = (ATT_HOST, ATT_PORT)
#-------------------------- CONSTANTS --------------------------

def sendrec(dev, msg):
    print(msg)
    dev.sendall(bytes(f'{msg}\n', encoding = 'utf8'))
    time.sleep(1)
    try:
        return_str = dev.recv(1024) 
    except socket.timeout:
        raise StopIteration('No data received from instrument') 
    return return_str
    
if __name__ == "__main__":

    ATT = socket.socket()
    ATT.connect(ATT_ADDRESS)
    ATT.settimeout(1)

    print(sendrec(ATT, ':CHAN:1:SETATT:0'))
    print(sendrec(ATT, 'ATT?'))
    time.sleep(5)

    for x in range(0,120):
        atten = x * 0.25 + 0.25
        print(sendrec(ATT, ':CHAN:1:SETATT:' + f'{atten}'))
        print(sendrec(ATT, 'ATT?'))
        time.sleep(5)


    ATT.close()
