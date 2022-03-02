# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 10:23:49 2020

@author: Rishad modifed by Sias 
@modify: Monde: 14-02-2022
        : Added the host and port numbers
        : Copied Power and Frequency from the NoiseIncreaseRev1.py
          for sig gen use only
Mod Gen ?
Modulation ?
"""

from re import S
import time
import socket

# The script uses raw ethernet socket communication, and thus VISA library/installation is not required

# -----------Connection Settings--------------
sigPORT = 5025             # default SMB R&S port 
sigHOST = '10.8.88.166'    #                        -- Section to be removed to a separate file
#---------------------------------------------


# --------------Initialization of Variables---
Power = 0.0                                 
Freq = 100e3    # Minimum 100kHz     
Zero = 0
One = 1
OFF = 'OFF'
ON = 'ON'
AM_Mod = 'AM'
FM_Mod = 'FM'
PM_Mod = 'PM'
# --------------------------------------------
         
default_timeout = 1

def initSigGen():
    """
    This function establishes a socket connection and identifies the instrument
    @params     : None
    """
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((sigHOST,sigPORT))
        s.settimeout(default_timeout)
        if s:
            print(s,"Connection succesful.")
    except Exception as e:
        print(e,"Check to see if the port number is {PORT}")
    s.sendall(b'*IDN?\r\n')                             
    data = s.recv(1024)
    #print('Received', data)
    sig_gen_id = data                           # for testing
    state=0
    setstate='OUTP1 {}\r\n'.format(state)       # Sets RF Output
    s.sendall(bytes(setstate, encoding='utf8'))
    s.sendall(b'OUTP1?\r\n')
    data=s.recv(1024)
    set_state = data                            # for testing
    #print('Received', data)
    s.close()
    if data.decode('utf8')=='1\n':      # 
        print("RF Output On")
    else: print("RF Output Off")

def setSigGenPower(power):
    """
    This function sets the power of the signal generator
    @param  Power: float
    """
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((sigHOST, sigPORT))
        s.settimeout(1)
    except Exception as e:
        print(e,"Check to see if the port number is {PORT}")
    setpower = 'POW {}\r\n'.format(power)
    s.sendall(bytes(setpower, encoding='utf8'))
    s.sendall(b'POW?\r\n')
    data = float(s.recv(1024))
    print("Sig gen power = %f dBm" %data)

def setSigGenFreq(Freq):
    """
    Identify instrument. Can be used as a connectivity check.
    """
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((sigHOST, sigPORT))
        s.settimeout(1)
    except Exception as e:
        print(e,"Check to see if the port number is {PORT}")
    setfreq= "FREQ {}\r\n".format(Freq)
    s.sendall(bytes(setfreq, encoding='utf8'))
    s.sendall(b'FREQ?\r\n')
    data = float(s.recv(1024))
    s.close()
    print(f"Sig gen frequency = {(data/1e6)} MHz")

def setSigGenState(RFOut):
    """
    This function turns on/off the RF output state
    @params RFOut:  Integer
    """
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((sigHOST, sigPORT))
        s.settimeout(1)
    except Exception as e:
        print(e,"Check to see if the port number is {PORT}")
    setstate='OUTP1 {}\r\n'.format(RFOut)
    s.sendall(bytes(setstate, encoding='utf8'))
    s.sendall(b'OUTP1?\r\n')
    data=s.recv(1024)
    print('Received', data, 'for RFOut')
    s.close()
    if data.decode("UTF-8") == "1\n":
        print("RF Output On")
    else: print(("RF Output Off"))

def setSigGenModsState(ModsState):
    """
    This function sets all modulation modes off
    @param ModsState: String
    """
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((sigHOST, sigPORT))
        s.settimeout(1)
    except Exception as e:
        print(e,"Check to see if the port number is {PORT}")
    setModsState='MOD:STAT {}\r\n'.format(ModsState)
    s.sendall(bytes(setModsState, encoding='utf8'))
    s.sendall(b'MOD:STAT?\n')
    data=s.recv(1024)
    print('Received', data)
    s.close()
    if data.decode("UTF-8") == "0\n":
        print("All modulations Off")
    else: print(("All modulations On"))

# ---------------------Modulations State Function-----------------------
def setSigGenModState(ModState, Val):
    """
    This function sets on different modulation schemes:
    @param  AM: string /
            PM: string /
            FM: string
    """
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((sigHOST, sigPORT))
        s.settimeout(1)
    except Exception as e:
        print(e,"Check to see if the port number is {PORT}")
    setModState='{}:STAT {}\r\n'.format(ModState, Val)
    s.sendall(bytes(setModState, encoding='utf8'))
    setModState='{}:STAT?\r\n'.format(ModState)
    s.sendall(bytes(setModState, encoding='utf8'))
    data=s.recv(1024)
    print('Received', data)
    s.close()
    if data.decode("UTF-8") == "1\n":
        print(f"{ModState} Modulation On")
    else: print(f"{ModState} Modulation On")

def LFOutputState(LFOState):            
    """
    This function sets the LFO Sweep Mode to Manual
    @param ModsState: String
    """
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((sigHOST, sigPORT))
        s.settimeout(1)
    except Exception as e:
        print(e,"Check to see if the port number is {PORT}")
    setLFOState='LFO:SWE:MODE?\r\n'
    s.sendall(bytes(setLFOState, encoding='utf8'))
    setLFOState='LFO {}\r\n'.format(LFOState)
    s.sendall(bytes(setLFOState, encoding='utf8'))
    s.sendall(b'LFO:SWE:MODE MAN\n')
    data=s.recv(1024)
    print('LFO:SWE:MODE Received', data)
    s.close()
    
# ---------------------Main Function-----------------------------------

def setupSigGen():
    initSigGen()                    # Get instrument ID
#    ----All settings off
    time.sleep(2)                   # Wait a bit
    setSigGenPower(Power)           # Set the power to 0dBm
    time.sleep(2)                   # Wait a bit
    setSigGenFreq(Freq)             # Set the power to 100kHz
    time.sleep(2)                   # Wait a bit
    setSigGenState(Zero)            # Turn off sig gen output
    time.sleep(2)                   # Wait a bit
    setSigGenModsState(OFF)         # Switch all modulations off
    time.sleep(2)                   # Wait a bit
    setSigGenModState(AM_Mod,OFF)   # Switch AM Modulation off
    time.sleep(2)                   # Wait a bit
    setSigGenModState(FM_Mod,OFF)   # Switch AM Modulation off
    time.sleep(2)                   # Wait a bit
    setSigGenModState(PM_Mod,OFF)   # Switch AM Modulation off
    time.sleep(2)                   # Wait a bit
    LFOutputState(OFF)              # Switch LFO off
    time.sleep(2)                   # Wait a bit

#   ----All settings on
    setSigGenPower(-25)             # Set the power to -25dBm
    time.sleep(2)                   # Wait a bit  
    setSigGenFreq(1500e6)           # Set the power to 1.5GHz
    time.sleep(2)                   # Wait a bit   
    setSigGenState(One)             # Turn on sig gen output
    time.sleep(2)                   # Wait a bit
    #setSigGenModsState(OFF)        # Switch all modulations on
    #time.sleep(5)                  # Wait a bit
    setSigGenModState(AM_Mod,ON)    # Switch AM Modulation on
    time.sleep(2)                   # Wait a bit
    setSigGenModState(AM_Mod,OFF)   # Switch AM Modulation off
    time.sleep(2)                   # Wait a bit
    setSigGenModState(FM_Mod,ON)    # Switch FM Modulation on
    time.sleep(2)                   # Wait a bit
    setSigGenModState(FM_Mod,OFF)   # Switch FM Modulation on
    time.sleep(2)                   # Wait a bit
    setSigGenModState(PM_Mod,ON)    # Switch FM Modulation on
    LFOutputState(ON)               # Switch LFO on

#    ----All settings off again
    time.sleep(5)                   # Wait a bit
    setSigGenPower(Power)           # Set the power to 0dBm
    time.sleep(5)                   # Wait a bit
    setSigGenFreq(Freq)             # Set the power to 100kHz
    time.sleep(5)                   # Wait a bit
    setSigGenState(Zero)            # Turn off sig gen output
    time.sleep(5)                   # Wait a bit
    setSigGenModsState(OFF)         # Switch all modulations off
    time.sleep(5)                   # Wait a bit
    setSigGenModState(AM_Mod,OFF)   # Switch AM Modulation off
    time.sleep(5)                   # Wait a bit
    setSigGenModState(FM_Mod,OFF)   # Switch AM Modulation off
    time.sleep(5)                   # Wait a bit
    setSigGenModState(PM_Mod,OFF)   # Switch AM Modulation off
    time.sleep(5)                   # Wait a bit    
    LFOutputState(OFF)              # Switch LFO off
    print("/------End of Setup signal generator---------/")

#%%   
# Main program
#-----------------------------------------------------------------------------    
print("/------Setup signal generator---------/")
setupSigGen()
