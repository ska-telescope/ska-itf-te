# -*- coding: utf-8 -*-
"""
Created on 1 April 2022

@author: benjamin Lunsky
            Setup Sig Gen Frequency and turn RF ON
"""

import time
import socket
import sys
import argparse

# -----------Connection Settings--------------
SG_PORT = 5025             # default SMB R&S port 
SG_HOST = '10.8.88.166'    # Sig gen IP
#---------------------------------------------


# --------------Initialization of Variables---
RF_OFF = 0
RF_ON = 1
DEFAULT_TIMEOUT = 1
OFF = "OFF"
ON = "ON"
# --------------------------------------------
         

def initSigGen(rfstate = RF_OFF):
    """
    This function establishes a socket connection and identifies the instrument
    @params     : None
    """
    
    try:
        
        sg = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #Connect to SG
        sg.connect((SG_HOST, SG_PORT))
        sg.settimeout(DEFAULT_TIMEOUT)
        if sg:
            print(sg, "Connection succesful.")
        else:
            print(sg, "Connection unsuccessful!") 
            sys.exit()                                      # Exit the code if unsuccessful
            
    except Exception as e:
        print(e, "Exception connecting to SG")
        
    sg.sendall(b'*IDN?\r\n')                                # Get system identification
    response = sg.recv(1024)
    print(response.decode('utf8'))
    
    sg.sendall(bytes('OUTP1 %i\r\n' % rfstate , encoding='utf8'))   # Sets RF Output OFF
    sg.sendall(b'OUTP1?\r\n')
    response = sg.recv(1024)
    
    if response.decode('utf8') == '1\n':      # 
        print("RF Output On")
    else: 
        print("RF Output Off")
    
    return sg

def setSigGenPower(sg, power = -10):
    """
    This function sets the power of the signal generator
    @param  sg
    @param  Power: integer
    """
    
    sg.sendall(bytes('POW %i\r\n' % power, encoding='utf8'))
    sg.sendall(b'POW?\r\n')
    response = float(sg.recv(1024))
    
    print("Sig gen power = %i dBm" % int(response))

def setSigGenFreq(sg, freq = 1e9):
    """
    Identify instrument. Can be used as a connectivity check.
    @param  sg
    @param  freq in Hz
    """
    
    sg.sendall(bytes("FREQ %i\r\n" % freq, encoding='utf8'))
    sg.sendall(b'FREQ?\r\n')
    response = float(sg.recv(1024))
    
    print(f"Sig gen frequency = %i MHz" % int(response/1e6))

def setSigGenRFOn(sg, rf_out = RF_ON):
    """
    This function turns on/off the RF output state
    @param  sg
    @params rfOut:  RF_ON or RF_OFF
    """

    sg.sendall(bytes('OUTP1 %i\r\n' % rf_out, encoding='utf8'))
    sg.sendall(b'OUTP1?\r\n')
    response = sg.recv(1024)
    
    if response.decode("UTF-8") == "1\n":
        print('RF is on')
    else: 
        print(("RF is off"))

def setSigGenModsStateOff(sg, mods_state = OFF):  
    """
    This function sets all modulation modes off
    @param  sg
    @param mods_state : String
    """

    sg.sendall(bytes('MOD:STAT %s\r\n' % mods_state, encoding='utf8'))
    sg.sendall(b'MOD:STAT?\n')
    data = sg.recv(1024)

    if data.decode("UTF-8") == "0\n":
        print("All modulations Off")
    else: print(("All modulations On"))

    
def setupSigGen(sg, power = -20, freq = 1e9, rf_out = RF_OFF):
    """
    This function sets up the sig gen - power, freq, rf on or off
    @param  sg
    @param power    : int
    @param freq     : int
    @param rf_out    : RF_ON or RF_OFF
    """    
    
    setSigGenModsStateOff(sg)       # Set all modes to off
    setSigGenPower(sg, power)       # Set power to specified level
    setSigGenFreq(sg, freq)         # Set frequency to specified level
    setSigGenRFOn(sg, rf_out)       # Set RF on or off
   
# ---------------------Main Function-----------------------------------

parser = argparse.ArgumentParser(description = "Specify Sig Gen Freq and Power and turn on RF Output")
parser.add_argument("power", type=int, help="the power level (dBm)")
parser.add_argument("freq", type=float, help="the frequency (Hz)")
args = parser.parse_args()

# Initiaslise the signal generator to a known state
sg = initSigGen()
# Set up sig gen to specified power and frequency and turn RF on
setupSigGen(sg, args.power, args.freq, RF_ON)

sg.close()
