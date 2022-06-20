# -*- coding: utf-8 -*-
'''
Created on Mon Feb 24 10:23:49 2020

@author: Rishad modifed by Sias 
@modify: Monde and Vhuli: 
        Date: 14-02-2022
        Affil: SKAO Test Engineers
        Description: 
        This script remotely controls basic settings of the signal generator
        There is no device connected at the sig gen output, the sig get is DUT
        Mods:
        Added the host and port numbers
        Copied Power and Frequency from the NoiseIncreaseRev1.py
        for sig gen use only
        Added funtion calls
'''

from re import S
import time
import socket

# The script uses raw ethernet socket communication, and thus VISA library/installation is not required

# -----------Connection Settings--------------
SG_PORT = 5025             # default SMB R&S port 
SG_HOST = '10.8.88.166'    # Sig gen IP                   
#---------------------------------------------


# --------------Initialization of Variables---
Power = 0.0                                 
Freq = 100e3    # Minimum 9 kHz     
ZERO = 0
ONE = 1
OFF = 'OFF'
ON = 'ON'
AM_MOD = 'AM'
FM_MOD = 'FM'
PM_MOD = 'PM'
DEFAULT_TIMEOUT = 1
# --------------------------------------------
         

def initSigGen():
    '''
    This function establishes a socket connection and identifies the instrument
    @params     : None
    '''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SG_HOST, SG_PORT))
        s.settimeout(DEFAULT_TIMEOUT)
        if s:
            print(s, 'Connection succesful.')
    except Exception as e:
        print(e, f'Check to see if the port number is {SG_PORT}')
    s.sendall(b'*IDN?\r\n')                             
    data = s.recv(1024)
    state = 0
    setstate = 'OUTP1 {}\r\n'.format(state)       # Sets RF Output
    s.sendall(bytes(setstate, encoding = 'utf8'))
    s.sendall(b'OUTP1?\r\n')
    data = s.recv(1024)
    s.close()
    if data.decode('utf8') == '1\n':       
        print('RF Output On')
    else: print('RF Output Off')

def setSigGenPower(power):
    ''' Set power

    This function sets the power of the signal generator
    @param:
        power: float in dBm
    '''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SG_HOST, SG_PORT))
        s.settimeout(1)
    except Exception as e:
        print(e, f'Check to see if the port number is {SG_PORT}')
    setpower = 'POW {}\r\n'.format(power)
    s.sendall(bytes(setpower, encoding = 'utf8'))
    s.sendall(b'POW?\r\n')
    data = float(s.recv(1024))
    print(f'Sig gen power = {data} dBm')

def setSigGenFreq(Freq):
    ''' Set frequency

    This function identifies the instrument. Can be used as a connectivity check.
    @params:
        frequency: float in Hz
    '''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SG_HOST, SG_PORT))
        s.settimeout(1)
    except Exception as e:
        print(e, f'Check to see if the port number is {SG_PORT}')
    setfreq = 'FREQ {}\r\n'.format(Freq)
    s.sendall(bytes(setfreq, encoding = 'utf8'))
    s.sendall(b'FREQ?\r\n')
    data = float(s.recv(1024))
    s.close()
    print(f'Sig gen frequency = {(data / 1e6)} MHz')

def setSigGenState(RFOut):
    ''' Set RF state

    This function turns on/off the RF output state
    @params:
        RFOut:  integer / string On/Off One/Zero
    '''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SG_HOST, SG_PORT))
        s.settimeout(1)
    except Exception as e:
        print(e, f'Check to see if the port number is {SG_PORT}')
    setstate = 'OUTP1 {}\r\n'.format(RFOut)
    s.sendall(bytes(setstate, encoding = 'utf8'))
    s.sendall(b'OUTP1?\r\n')
    data = s.recv(1024)
    print(f'Received {data} for RFOut')
    s.close()
    if data.decode('UTF-8') == '1\n':
        print('RF Output On')
    else: print('RF Output Off')

def setSigGenModsState(ModsState):
    ''' Set All Modulation States

    This function sets all modulation modes off
    @param:
        ModsState: String On/Off
    '''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SG_HOST, SG_PORT))
        s.settimeout(1)
    except Exception as e:
        print(e, f'Check to see if the port number is {SG_PORT}')
    setModsState = 'MOD:STAT {}\r\n'.format(ModsState)
    s.sendall(bytes(setModsState, encoding = 'utf8'))
    s.sendall(b'MOD:STAT?\n')
    data = s.recv(1024)
    print(f'Received {data}')
    s.close()
    if data.decode('UTF-8') == '0\n':
        print('All modulations Off')
    else: print('All modulations On')

# ---------------------Modulations State Function-----------------------
def setSigGenModState(ModState, Val):
    ''' Set Modulation Scheme

    This function sets on different modulation schemes:
    @param:
        AM: string /
        PM: string /
        FM: string
    '''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SG_HOST, SG_PORT))
        s.settimeout(1)
    except Exception as e:
        print(e, f'Check to see if the port number is {SG_PORT}')
    setModState = '{}:STAT {}\r\n'.format(ModState, Val)
    s.sendall(bytes(setModState, encoding = 'utf8'))
    setModState = '{}:STAT?\r\n'.format(ModState)
    s.sendall(bytes(setModState, encoding = 'utf8'))
    data = s.recv(1024)
    print(f'Received {data}')
    s.close()
    if data.decode('UTF-8') == '1\n':
        print(f'{ModState} Modulation On')
    else: print(f'{ModState} Modulation On')

def LFOutputState(LFOState):            
    ''' Set Low Frequency State

    This function sets the LFO Sweep Mode to Manual
    @params:
        LFOState: String On/Of
    '''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SG_HOST, SG_PORT))
        s.settimeout(1)
    except Exception as e:
        print(e, f'Check to see if the port number is {SG_PORT}')
    setLFOState = 'LFO:SWE:MODE?\r\n'
    s.sendall(bytes(setLFOState, encoding = 'utf8'))
    setLFOState = 'LFO {}\r\n'.format(LFOState)
    s.sendall(bytes(setLFOState, encoding = 'utf8'))
    s.sendall(b'LFO:SWE:MODE MAN\n')
    data = s.recv(1024)
    print(f'LFO:SWE:MODE Received {data}')
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
    setSigGenState(ZERO)            # Turn off sig gen output
    time.sleep(2)                   # Wait a bit
    setSigGenModsState(OFF)         # Switch all modulations off
    time.sleep(2)                   # Wait a bit
    setSigGenModState(AM_MOD, OFF)   # Switch AM Modulation off
    time.sleep(2)                   # Wait a bit
    setSigGenModState(FM_MOD, OFF)   # Switch AM Modulation off
    time.sleep(2)                   # Wait a bit
    setSigGenModState(PM_MOD, OFF)   # Switch AM Modulation off
    time.sleep(2)                   # Wait a bit
    LFOutputState(OFF)              # Switch LFO off
    time.sleep(2)                   # Wait a bit

#   ----All settings on
    setSigGenPower(-25)             # Set the power to -25dBm
    time.sleep(2)                   # Wait a bit  
    setSigGenFreq(1500e6)           # Set the power to 1.5GHz
    time.sleep(2)                   # Wait a bit   
    setSigGenState(ONE)             # Turn on sig gen output
    time.sleep(2)                   # Wait a bit
    setSigGenModState(AM_MOD, ON)    # Switch AM Modulation on
    time.sleep(2)                   # Wait a bit
    setSigGenModState(AM_MOD, OFF)   # Switch AM Modulation off
    time.sleep(2)                   # Wait a bit
    setSigGenModState(FM_MOD, ON)    # Switch FM Modulation on
    time.sleep(2)                   # Wait a bit
    setSigGenModState(FM_MOD, OFF)   # Switch FM Modulation on
    time.sleep(2)                   # Wait a bit
    setSigGenModState(PM_MOD, ON)    # Switch FM Modulation on
    LFOutputState(ON)               # Switch LFO on

#    ----All settings off again
    time.sleep(5)                   # Wait a bit
    setSigGenPower(Power)           # Set the power to 0dBm
    time.sleep(5)                   # Wait a bit
    setSigGenFreq(Freq)             # Set the power to 100kHz
    time.sleep(5)                   # Wait a bit
    setSigGenState(ZERO)            # Turn off sig gen output
    time.sleep(5)                   # Wait a bit
    setSigGenModsState(OFF)         # Switch all modulations off
    time.sleep(5)                   # Wait a bit
    setSigGenModState(AM_MOD,OFF)   # Switch AM Modulation off
    time.sleep(5)                   # Wait a bit
    setSigGenModState(FM_MOD,OFF)   # Switch AM Modulation off
    time.sleep(5)                   # Wait a bit
    setSigGenModState(PM_MOD,OFF)   # Switch AM Modulation off
    time.sleep(5)                   # Wait a bit    
    LFOutputState(OFF)              # Switch LFO off
    print('/------End of Setup signal generator---------/')

#%%   
# Main program
#-----------------------------------------------------------------------------    
print('/------Setup signal generator---------/')
setupSigGen()
