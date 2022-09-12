#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: Ben/Vhuli/Monde 
@Date: xx-09-2022
@Affiliation: Test Engineers
@Functional Description: 
    1. This script generates a frequency sweep from 100 MHz to 2 GHz at 100 MHz steps
    2. The parameters can be adjusted as per user requirements
    3. Where it applies SG denotes Signal Generator 
    4. Run the script by parsing the following arguments on the terminal:
        - start frequency = 100000000 or 100e6, integer with no units [100 MHz]
        - stop frequency = 2000000000 or 2e9, integer with no units [2 GHz]
        - step frequency = 100000000 or 100e6, integer with no units [100 MHz]
        - dwell time = 1000, integer with no units [ms]
@Notes: 
    1. This script was written for the SMB100A Signal Generator. Raw ethernet socket communication is used
        and thus VISA library/installation is not required
    2. This script uses scpi protocol for the automatic test equipment intended

@modifier: Monde
@Date: 12-09-2022
    1. Replaced raw commands with database lookups 
    2. File renaming to sg_smb100a_generate_frequency_sweep_2.py
@Revision: 2
'''
import sys
import os
import time
import socket
import argparse
sys.path.insert(1, os.path.abspath(os.path.join('../../') + '/resources/'))
from scpi_database import SGCmds
# -----------------Connection Settings----------------------
SG_PORT = 5025                      # default SMB R&S port 
SG_HOST = '10.20.7.1'             # smb100a signal generator IP
SG_ADDRESS = (SG_HOST, SG_PORT)
#---------------------------------------------------------------
#-------------------------- CONSTANTS --------------------------

step_freq = 3015873             # step frequency in MHz
DEFAULT_TIMEOUT = 1             # Default socket timeout
RECDUR = 5                      # Time in seconds to find maxhold peaks
RESPONSE_TIMEOUT = 0.01

DEFAULT_BUFFER = 1024
SHORT_DELAY = 0.1
LONG_DELAY = 1
RF_OFF = 0
RF_ON = 1
# ---------------- Look up table ---------------------------

# --------------------------------------------

class SG_SOCK(socket.socket):
    def __init__(self):
        socket.socket.__init__(self)                # Object init
        self.delay_long_s = LONG_DELAY
        self.delay_short_s = SHORT_DELAY
        self.default_buffer = DEFAULT_BUFFER 
        self.response_timeout = RESPONSE_TIMEOUT

    def connectSG(self, SA_ADDRESS):
        ''' Establish socket connect connection.

        This function:
            - Establishes a socket connection to the Spectrum Analyzer. Uses address (Including Port Number) as an argument.
            - Sets the Display to On in Remote mode
        @params 
        SA_ADDRESS         : specHOST str, specPORT int
        '''    
        self.connect(SA_ADDRESS)  # connect to spectrum analyzer via socket and Port
        self.settimeout(self.response_timeout) 
        print(f'Connected to: {self.getSGCmd(SGCmds["device-id"]).decode()}')
        
    def getSGCmd(self, request_str, response_buffer = 'default', timeout_max = 10, param = ''):
        ''' Request data

        This function requests and reads the command to and from the test device
        @params:
            request_str  : string
        ''' 
        if type(response_buffer) == str:
            response_buffer = self.default_buffer                   # Cleanup the receive buffer
                                                
        if param == '':
            self.setSGCmd(f'{request_str}?')                        # Send the request, adds a question mark for a get/read command
        else:
            self.setSGCmd(f'{request_str}? {param}')                # Send the request, adds a question mark for a get/read command, and adds a command
        
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

    def setSGCmd(self, command_str, param = ''):
        ''' Send command
        
        This function sends the command and adds \n at the end of any commands 
        sent to the test device
        @params:
            command_str  : string    
        '''
        if param == '':
            self.sendall(bytes(command_str, encoding = 'utf8') + b'\n')    
        else:
            self.sendall(bytes(command_str, encoding = 'utf8') + bytes(f' {param}\n', encoding = 'utf8'))
        time.sleep(self.response_timeout)

        # for every set, invoke a get to confirm parameter is set
        # Check with Ben/Vhuli for a generic way of 'get'

    def closeSG(self):
        self.setSGCmd(SGCmds['rf-state'], RF_OFF)
        self.close()
        print('Signal Generator socket Disconnected')

# ---------------------------------------------------
# End of Signal Generator class
# ---------------------------------------------------
#%%   
# Main program
# -----------------------
if __name__ == '__main__':
    # Set up arguments to be parsed 
    parser = argparse.ArgumentParser(description = 'Specify Sig Gen Start Frequency, Stop Frequency, Step Frequency and Dwell Time')
    parser.add_argument('start_freq', type = str, help = 'the start frequency incl. units (Hz)')
    parser.add_argument('stop_freq', type = str, help = 'the stop frequency incl. units (Hz)')
    parser.add_argument('step_freq', type = str, help = 'the step frequency incl. units (Hz)')
    parser.add_argument('dwel_time', type = int, help = 'the sweep dwell time (ms)')
    args = parser.parse_args()

    print("/------Setup Signal Generator ---------/")
    SG = SG_SOCK()
    SG.connectSG(SG_ADDRESS)
    # Set Power 
    SG.setSGCmd(SGCmds['power'], -20)   # constant
    SG.setSGCmd(SGCmds['rf-state'], RF_ON)
    '''
        This block of code generate a sweep frequency of the signal generator
        at 100MHz step
        @params:
            start_freq      : start frequency in Hz (not less than 9 kHz)
            stop_freq       : stop frequency in Hz (not more than 6 GHz)
            step_freq       : step frequency in Hz (default = 100 MHz)
            dwel_time       : duration of frequency output in ms (default=1000 ms)
            sweep_mode      : sweep mode (auto / manual)
        ''' 
    centFreq = (int(float(args.start_freq)) + int(float(args.stop_freq))) / 2
    span = int(float(args.stop_freq)) - int(float(args.start_freq))    
        # 1. Set the sweep range
    SG.setSGCmd(SGCmds['cent-freq'], f'{centFreq}')
    print('Centre frequency' + SGCmds['cent-freq'], f'{centFreq}')
    SG.setSGCmd(SGCmds['span-freq'], f' {span}')
        # 2. Select linear or logarithmic spacing
    SG.setSGCmd(SGCmds['sweep-freq-spac-conf'], 'LIN')
        # 3. Set the step width and dwell time
    SG.setSGCmd(SGCmds['sweep-freq-step'], f'{args.step_freq}')
    SG.setSGCmd(SGCmds['sweep-freq-dwell'], f'{args.dwel_time}')
        # 4. Select the trigger mode
    SG.setSGCmd(SGCmds['sweep-freq-trig'], 'SING')
        # 5. Select sweep mode and activate the sweep
    SG.setSGCmd(SGCmds['sweep-freq-mode'], 'AUTO')
    SG.setSGCmd(SGCmds['freq-mode'], 'SWE')
        # 6. Trigger the sweep     
    SG.setSGCmd(SGCmds['sweep-freq-exec'])
    print('Executing sweep...')
    # SG.closeGenSock() # Socket closed at top-level