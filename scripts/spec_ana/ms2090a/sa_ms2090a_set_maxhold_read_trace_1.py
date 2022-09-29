#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Ben/Vhuli/Monde 
@Date: xx-09-2022
@Affiliation: 
@Functional Description: 
    1. This script sets / gets spectrum analyzer parameters of the Anritsu MS2090A Spectrum Analyzer
 
@Notes: 
    1. This script was written for the MS2090A Spectrum Analyzer. 
        Raw ethernet socket communication is used and thus VISA library/installation is not required

@Revision: 1 
"""

#-------------------------- IMPORT REQUIRED PACKAGES-------------------------------------
import sys
import os
import socket
import time
sys.path.insert(1, os.path.abspath(os.path.join('../../') + '/resources/'))
from scpi_database import SACmds

# -------------------------- CONNECTION SETTINGS -------------------------------------------
SA_HOST = '10.20.7.4'         # MS2090A spectrum analyzer IP
SA_PORT = 9001                # MS2090A spectrum analyzer port
SA_ADDRESS = (SA_HOST, SA_PORT)
#-------------------------- CONSTANTS --------------------------

FREQ_STEP = 3015873             # step frequency in MHz
DEFAULT_TIMEOUT = 1             # Default socket timeout
RECDUR = 5                      # Time in seconds to find maxhold peaks
RESPONSE_TIMEOUT = 0.01
SPEC_ANA_MODE = 'SPEC'

DEFAULT_BUFFER = 1024
SHORT_DELAY = 0.1
LONG_DELAY = 1

#-------------------------SPECTRUM ANALYZER SOCKET CLASS----------------------------------
class SA_SOCK(socket.socket):
    def __init__(self):
        socket.socket.__init__(self)             # Object init
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
        specAddress         : specHOST str, specPORT int
        '''    
        self.settimeout(DEFAULT_TIMEOUT) 
        self.connect(SA_ADDRESS)  # connect to spectrum analyzer via socket and Port
        print(f'Connected to: {self.getSACmd(SACmds["device-id"])}')

    def getSACmd(self, request_str, param = '', response_buffer = DEFAULT_BUFFER, timeout_max = 10):
        ''' Request data

        This function requests and reads the command to and from the test device
        @params:
            request_str  : string
            param        : string
        '''                       
        print(f'{request_str}' + f'? {param}')              
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

    def closeSA(self):
        self.close()
        print('Spectrum Analyzer socket Disconnected')