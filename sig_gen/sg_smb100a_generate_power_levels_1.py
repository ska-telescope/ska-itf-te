#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: Vhuli / Monde 
@Date: 20-06-2022
@Affiliation: Test Engineers
@Functional Description: 
    1. This script generates power or frequency values as per user settings 
    
@Notes: 
    1. This script was written for the SMB100A Signal Generator. Raw ethernet socket communication is used
        and thus VISA library/installation is not required
    2. This script uses scpi protocol for the automatic test equipment intended

@Revision: 1
'''

import time
import socket
import argparse
from scpi_database import sig_gen_scpi_cmds, common_scpi_cmds

# -----------------Connection Settings----------------------
SG_PORT = 5025                      # default SMB R&S port 
SG_HOST = '10.8.88.166'             # smb100a signal generator IP
SG_ADDRESS = (SG_HOST, SG_PORT)
#-----------------------------------------------------------
# ----------------Initialization of Variables---------------    
DEFAULT_TIMEOUT = 1        # Default socket timeout
RF_OFF = 0
RF_ON = 1
RESPONSE_TIMEOUT = 0.01

dump_str = ''
freq_start = ''
freq_stop = ''
power = []
# --------------------------------------------

class SG_SOCK(socket.socket):
    def connectSigGen(self, SG_ADDRESS, DEFAULT_TIMEOUT = 1, default_buffer = 1024, short_delay = 0.1, long_delay = 1):
        ''' Establish socket connection.

        This function:
            Establishes a socket connection to the Signal Generator. Uses address (Including Port Number) as an argument.
            Performs a reset on the unit and sets the fixed frequency generator mode. 
            Sets the Display to On in Remote mode
            @params 
                sigAddress         :   sigHOST str IP address of the device
                                    sigPORT int port number to device access
                default_timeout     : int Timeout for waiting to establish connection
                long_delay          : int
                short_delay         : int
                default_buffer      : int
        '''
        try:
            self.connect(SG_ADDRESS)                                
            self.settimeout(DEFAULT_TIMEOUT)
            self.delay_long_s = long_delay
            self.delay_short_s = short_delay
            self.default_buffer = default_buffer
            rx_str = self.requestSigGenData('*IDN?')
            print(f'Connected to: {rx_str}')
            self.sendSigGenCmd(common_scpi_cmds['clear_status'])                                     
            self.sendSigGenCmd(common_scpi_cmds['reset']) 
            self.sendSigGenCmd('SYST:DISP:UPD ON')
            time.sleep(short_delay)
        except Exception as e:
            print(e, f'Check to see if the port number is {SG_PORT}')

    def dumpSigGenData(self): 
        ''' Display received data.

        This function receives and displays the data after a query command
        @params: 
            command  : string    
        '''
        while True:
            try:
                dump_str = self.recv(self.default_buffer)
                print(f'Dumping buffer data: {dump_str}')
            except socket.timeout:
                break

    def sendSigGenCmd(self, command_str):
        ''' Send command.

        This function sends the command and adds \n at the end of any commands 
            sent to the test device
        @params: 
            command  : scpi string   
        '''
        self.sendall(bytes(command_str, encoding = 'utf8'))
        self.sendall(bytes('\n', encoding = 'utf8'))
        time.sleep(RESPONSE_TIMEOUT)

    def requestSigGenData(self, request_str, response_buffer = 'default', timeout_max = 20):
        ''' Request data.

        This function requests and reads the command to and from the test device
        @params:
            command  : scpi string  
        ''' 
        if type(response_buffer) == str:
            response_buffer = self.default_buffer
        self.dumpSigGenData()                                         # Cleanup the receive buffer
        self.sendSigGenCmd(request_str)                           # Send the request
        return_str = b''                                            # Initialize Rx buffer
        time_start = time.time()                                   # Get the start time
        while True:
            time.sleep(self.delay_short_s)                         # Introduce a short delay
            try:
                return_str += self.recv(response_buffer)           # Attempt to read the buffer
            except socket.timeout:
                if (time.time() - time_start) > timeout_max:
                       raise StopIteration('No data received from instrument') 
                else:
                    time.sleep(self.delay_short_s)                
            else:
                if return_str.endswith(b'\n'):                  
                    return return_str[:-1] 

    def setSigGenRF(self, rf_state = RF_ON):
        ''' Set RF output.

        This function sets and returns the RF Status
            @params:
                rf_state  : Sig gen RF output as On or Off
            @returns:
                rf_state  : Sig gen RF status as On or Off
        '''
        self.sendSigGenCmd(f'OUTP {rf_state}')  
        dump_str = self.requestSigGenData('OUTP?')
        if dump_str == b'1':   
            print('RF Output On')
        else: print('RF Output Off')

    def setSigGenPower(self, power):
        ''' Set power.

        This function sets the power of the signal generator
        @params:
            power   : power level in dBm (default = -30)
        '''
        self.sendSigGenCmd(f'POW {power}')
        data = self.requestSigGenData('POW?')
        power = float(data.decode())
        print(f'Sig gen power = {power} dBm')  
        return power

    def setSigGenFreq(self, frequency):
        ''' Set frequency.

        This function sets the frequency of the signal generator
        @params:
            frequency   : frequency in Hz (default = 1 GHz)
        '''
        self.sendSigGenCmd(f'FREQ {frequency}')
        data = self.requestSigGenData('FREQ?')
        print(f'Signal Generator Frequency = {float(data.decode()) / 1e6} MHz')  

    def closeSigGenSock(self):
        self.close()
        print('Signal Generator socket Disconnected')

# ---------------------------------------------------
# End of Signal Generator class
# ---------------------------------------------------