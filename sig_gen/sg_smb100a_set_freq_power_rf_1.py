#!/usr/bin/env python3


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
         

def initSigGen():
    '''
    This function establishes a socket connection and returns the active socket connection
        
        Parameters:
            rf_state (int)  : RF_ON or RF_OFF
    
        Returns:
            sg              : Sig gen socket connection
    '''
    
    try:
        
        sg = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #Connect to SG
        sg.connect((SG_HOST, SG_PORT))
        sg.settimeout(DEFAULT_TIMEOUT)
        if sg:
            print(sg, "\nConnection succesful.\n\n")
        else:
            print(sg, "\nConnection unsuccessful!\n\n") 
            sys.exit()                                      # Exit the code if unsuccessful
            
    except Exception as e:
        print(e, "Exception connecting to SG")

    return sg                                               # Returns sig gen socket
    
def getSigGenIDN(sg):
    '''
    This function returns the Sig Gen IDN
        
        Parameters:
            sg              : socket connection
    
        Returns:
            IDN              : Sig gen IDN response as string
    '''    

    sg.sendall(b'*IDN?\r\n')                                # Get system identification
    response = sg.recv(1024)
    
    return response.decode('utf8')



def getSigGenRFState(sg):
    '''
    This function returns the Sig Gen RF Status
        
        Parameters:
            sg              : socket connection
    
        Returns:
            RF Status       : Sig gen RF Status as RF_ON or RF_OFF
    '''        
    

    sg.sendall(b'OUTP1?\r\n')
    response = sg.recv(1024)
    
    if response.decode('utf8') == '1\n':      # 
        return RF_ON
    else: 
        return RF_OFF
    

def setSigGenPower(sg, power = -10):
    '''
    This function sets the power of the signal generator
        
        Parameters:
            sg              : socket connection
            power           : power level in dBm (default = -10)

    '''    
    
    sg.sendall(bytes('POW %i\r\n' % power, encoding='utf8'))
    sg.sendall(b'POW?\r\n')
    response = float(sg.recv(1024))
    
    print("Sig gen power = %i dBm" % int(response))

def setSigGenFreq(sg, freq = 1e9):
    '''
    This function sets the frequency of the signal generator
        
        Parameters:
            sg (socket)
            freq           : frequency in Hz (default = 1e9 or 1 GHz)

    '''    
    
    sg.sendall(bytes("FREQ %i\r\n" % freq, encoding='utf8'))
    sg.sendall(b'FREQ?\r\n')
    response = float(sg.recv(1024))
    
    print(f"Sig gen frequency = %i MHz" % int(response/1e6))

def setSigGenRF(sg, rf_out = RF_ON):
    '''
    This function sets the RF output to on or off
        
        Parameters:
            sg              : socket connection
            rf_out          : RF_ON or RF_OFF (default RF_ON)

    '''    

    sg.sendall(bytes('OUTP1 %i\r\n' % rf_out, encoding='utf8'))
<<<<<<< HEAD
    sg.sendall(b'OUTP1?\r\n')
    response = sg.recv(1024)
    
    if response.decode("UTF-8") == "1\n":
=======
    
    if getSigGenRFState(sg) == RF_ON:
>>>>>>> 68e3b575b872b686f0bfc315701ee74069b3e319
        print('RF is on')
    else: 
        print(("RF is off"))

def setSigGenModsStateOff(sg, mods_state = OFF):  
    '''
    This function sets the modulation modes off
        
        Parameters:
            sg              : socket connection
            mods_state      : modulation state (default OFF)

    '''    

    sg.sendall(bytes('MOD:STAT %s\r\n' % mods_state, encoding='utf8'))  #Turn mods states off
    sg.sendall(b'MOD:STAT?\n')
    data = sg.recv(1024)

    if data.decode("UTF-8") == "0\n":
        print("All modulations Off")
    else: print(("All modulations On"))

    
def setSigGen(sg, power = -20, freq = 1e9, rf_out = RF_ON):
    '''
    This function sets the power, frequency and RF on or off
        
        Parameters:
            sg              : socket connection
            power           : power level to be set in dBm (default -20)
            freq            : freq level to be set in Hz (default 1e9)
            rf_out          : RF_ON or RF_OFF (default RF_ON)

    '''        
    
    print("IDN : %s" % getSigGenIDN(sg))    # Get IDN of SG
        
    if getSigGenRFState(sg) == RF_ON:      # Check RF status
        print("RF is on\n")
    else:
        print("RF is off\n")
    
    setSigGenModsStateOff(sg)       # Set all modes to off
    setSigGenPower(sg, power)       # Set power to specified level
    setSigGenFreq(sg, freq)         # Set frequency to specified level
    setSigGenRF(sg, rf_out)         # Set RF on or off
   
# ---------------------Main Function-----------------------------------

if __name__ == '__main__':
    
    # Set up arguments to be parsed 
    parser = argparse.ArgumentParser(description = "Specify Sig Gen Freq and Power and turn on RF Output")
    parser.add_argument("power", type=int, help="the power level (dBm)")
    parser.add_argument("freq", type=float, help="the frequency (Hz)")
    args = parser.parse_args()

    # Initiaslise the signal generator to a known state
    sg = initSigGen()
    # Set up sig gen to specified power and frequency and turn RF on
    setSigGen(sg, args.power, args.freq)
    # Close socket to SG
    sg.close()
