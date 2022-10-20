#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Ben/Vhuli/Monde 
@Date: 26-09-2022
@Affiliation: 
@Functional Description: 
    1. This script reads the basic parameters of the Anritsu MS2090A Spectrum Analyzer
    2. Run the script by parsing the following arguments on the terminal:
        - start frequency = 0 or 100e6, integer with no units [0 Hz]
        - stop frequency = 2000000000 or 3e9, integer with no units [3 GHz]
 
@Notes: 
    1. This script was written for the MS2090A Spectrum Analyzer. 
        Raw ethernet socket communication is used and thus VISA library/installation is not required

@Revision: 1
"""

#-------------------------- IMPORT REQUIRED PACKAGES-------------------------------------

import socket
import time
import argparse
import os, sys
sys.path.insert(2, os.path.abspath(os.path.join('../../../') + '/resources/'))
#sys.path.insert(1, os.path.abspath(os.path.join('../../') + '/resources/')) # for the notebook

from scpi_database import SACmds

# -------------------------- CONNECTION SETTINGS -------------------------------------------
SA_HOST = 'za-itf-spectrum-analyser.ad.skatelescope.org'  # '10.20.7.4'         # MS2090A spectrum analyzer IP
SA_PORT = 9001                # MS2090A spectrum analyzer port
SA_ADDRESS = (SA_HOST, SA_PORT)
#-------------------------- CONSTANTS --------------------------

DEFAULT_TIMEOUT = 1             # Default socket timeout
RECDUR = 5                      # Time in seconds to find maxhold peaks
RESPONSE_TIMEOUT = 0.01
SPEC_ANA_MODE = 'SPEC'

DEFAULT_BUFFER = 1024
SHORT_DELAY = 0.1
LONG_DELAY = 1
# ----------------Initialization of Variables---------------    

# ---------------- Look up table ---------------------------

#-------------------------SPECTRUM ANALYZER SOCKET CLASS----------------------------------
class SA_SOCK(socket.socket):

    def __init__(self):
        socket.socket.__init__(self)                # Object init
        self.delay_long_s = LONG_DELAY
        self.delay_short_s = SHORT_DELAY
        self.default_buffer = DEFAULT_BUFFER 
        self.response_timeout = RESPONSE_TIMEOUT

    def connectSA(self, SA_ADDRESS):
        ''' Establish socket connect connection.

        This function:
            - Establishes a socket connection to the Spectrum Analyzer. Uses address (Including Port Number) as an argument.
            - Sets the Display to On in Remote mode
        @params 
        SA_ADDRESS         : specHOST str, specPORT int
        '''    
        self.connect(SA_ADDRESS)  # connect to spectrum analyzer via socket and Port
        self.settimeout(self.response_timeout) 
        return self.getSACmd(SACmds['device_id']).decode()
        # return self.getSACmd(SACmds['device_id'])
        
    def getSACmd(self, request_str, response_buffer = DEFAULT_BUFFER, timeout_max = 10, param = ''):
        ''' Request data

        This function requests and reads the command to and from the test device
        @params:
            request_str  : string
        '''                                     
        self.sendall(bytes(request_str + f'? {param}\n', encoding = 'utf8'))
        time.sleep(self.response_timeout) 
        return_str = b''                                            # Initialize Rx buffer
        time_start = time.time()                                    # Get the start time
        
        while True:
            time.sleep(self.delay_short_s)                          # Introduce a short delay
            try:
                return_str += self.recv(response_buffer)            # Attempt to read the buffer
            except socket.timeout:
                if (time.time() - time_start) > timeout_max:
                    raise StopIteration('No data received from instrument') 
                else:
                    time.sleep(self.delay_short_s)                  # No response, keep waiting
            else:
                if return_str.endswith(b'\n'):                      # Test to see if end of line has been reached, i.e. all the data Rx
                    return return_str[:-1]  

    def setSACmd(self, command_str, param = ''):
        ''' Send command
        
        This function sends the command and adds \n at the end of any commands 
        sent to the test device
        @params:
            command_str  : string    
        '''
        self.sendall(bytes(command_str + f' {param}\n', encoding = 'utf8'))
        time.sleep(self.response_timeout)        

    def setSACmdResponse(self, command_str, param = ''):
        ''' Send command
        
        This function sends the command and adds \n at the end of any commands 
        sent to the test device and returns getSACmd to verify the value was set correctly
        @params:
            command_str  : string    
        '''
        self.sendall(bytes(command_str + f' {param}\n', encoding = 'utf8'))
        time.sleep(self.response_timeout)        
        return self.getSACmd(command_str)

    def closeSASock(self):
        self.close()

if __name__ == '__main__':
    # Set up arguments to be parsed 
    parser = argparse.ArgumentParser(description = 'Specify Start and Stop Frequency')
    parser.add_argument('start_freq', type = str, help = 'the start frequency incl. units (Hz)')
    parser.add_argument('stop_freq', type = str, help = 'the stop frequency incl. units (Hz)')
    args = parser.parse_args()

    print("/------Setup spectrum analyser---------/")
    SA = SA_SOCK()
    print(SA.connectSA(SA_ADDRESS))
    SA.setSACmd(SACmds['reset_device'])  
    SA.setSACmd(SACmds['clear_status']) 

    # Configure measurement mode to Spectrum
    spec_ana_mode = SA.setSACmdResponse(SACmds['device_mode'], SPEC_ANA_MODE).decode()
    if spec_ana_mode != SPEC_ANA_MODE:
        print("Error setting Spectrum Analyser Mode")
    else: print(f'Spectrum Analyzer Mode set to Spectrum') 

    # Set start frequency of spectrum analyzer
    start_freq = float(SA.setSACmdResponse(SACmds['start_freq'], args.start_freq).decode())
    if start_freq != float(args.start_freq):              # set start freq, check response
        print("Error setting Spectrum Analyzer Start Freq")
    else: print(f'Start Frequency = {start_freq / 1e6} MHz')
    
    # Set stop frequency of spectrum analyzer
    stop_freq = float(SA.setSACmdResponse(SACmds['stop_freq'], args.stop_freq).decode())
    if stop_freq != float(args.stop_freq):              # set stop freq, check response
        print("Error setting Spectrum Analyser Start Freq")
    else: print(f'Stop Frequency = {stop_freq / 1e6} MHz')

    SA.close()
