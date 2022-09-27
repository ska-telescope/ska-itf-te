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
import unittest
import os, sys
sys.path.insert(2, os.path.abspath(os.path.join('../../../') + '/resources/'))
from scpi_database import SACmds

# -------------------------- CONNECTION SETTINGS -------------------------------------------
SA_HOST = '10.20.7.4'         # MS2090A spectrum analyzer IP
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
        return self.getSACmd(SACmds["device-id"]).decode()
        
    def getSACmd(self, request_str, response_buffer = DEFAULT_BUFFER, timeout_max = 10, param = ''):
        ''' Request data

        This function requests and reads the command to and from the test device
        @params:
            request_str  : string
        '''                                     
        self.setSACmd(f'{request_str}? {param}')                    # Send the request, adds a question mark for a get/read command, and adds a command
        
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

    def setSACmd(self, command_str, param = '', returnval = False):
        ''' Send command
        
        This function sends the command and adds \n at the end of any commands 
        sent to the test device
        @params:
            command_str  : string    
        '''
        self.sendall(bytes(command_str, encoding = 'utf8') + bytes(f' {param}\n', encoding = 'utf8'))
        time.sleep(self.response_timeout)        

    def test_function(self, expected_param, parsed_param):
        expression_false = expected_param != parsed_param
        if expression_false:
            unittest.TestCase.assertFalse(expression_false, False) # test Fail
            print('Test Fail')
        
        expression_true = expected_param = parsed_param
        if expression_true:
            unittest.TestCase.assertTrue(expression_true, True)      # test Pass
            print('Test Pass')

    def closeSpecAna(self):
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
    SA.setSACmd(SACmds['reset-device'])  # Reset
    SA.setSACmd(SACmds['clear-status'])
    SA.setSACmd(SACmds['device-mode'], SPEC_ANA_MODE)

    SA.setSACmd(SACmds['start-freq'], args.start_freq)                  # set start freq
    expected_start_freq = int(SA.getSACmd(SACmds["start-freq"]).decode())
    print(f'Start Frequency = {float(expected_start_freq)/1e6} MHz')
    # Test whether start frequency is what was set
    SA.test_function(expected_start_freq, float(args.start_freq))     # test start frequency 
    
    SA.setSACmd(SACmds['stop-freq'], args.stop_freq)                    # set stop freq
    expected_stop_freq = int(SA.getSACmd(SACmds["stop-freq"]).decode())
    print(f'Stop Frequency = {float(expected_stop_freq)/1e9} GHz')
    # Test whether stop frequency is what was set
    SA.test_function(float(expected_stop_freq), float(args.stop_freq))     # test start frequency 

    SA.close()
