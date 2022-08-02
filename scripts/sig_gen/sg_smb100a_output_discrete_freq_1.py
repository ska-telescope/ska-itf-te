#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: Monde 
@Date: 24-03-2022
@Affiliation: Test Engineer
@Functional Description: 
    1. This script generates discrete frequencies of SMB100A Sig Gen from
        100 MHz to 2.3 GHz at 100 MHz steps
    2. The steps frequency can be adjusted as per user requirements
    3. The script uses raw ethernet socket communication, and thus VISA 
        library/installation is not required
    4. This script uses scpi protocol for ATE
    5. Where it applies sg denotes Signal Generator   
@Revision: 1
'''

import time
import socket

# -----------------Connection Settings-------------------
SG_PORT = 5025             # default SMB R&S port 
SG_HOST = '10.8.88.166'    # Sig gen IP  
SG_ADDRESS = (SG_HOST, SG_PORT)
#--------------------------------------------------------
# ----------------Initialization of Variables------------
Power = -30.0                   # Start RefLev [dBm]                              
Freq = 900e3                    # Start frequency Minimum 100kHz     
DEFAULT_TIMEOUT = 1             # Default socket timeout
rf_state = 0                    # Default RF Out state
# --------------------Constants-------------------------
ON = 'ON'
OFF = 'OFF'
# -----------Global Variables---------------------------
dump_str = ''

class sig_sock(socket.socket):
    def connectSigGen(self, SG_ADDRESS, DEFAULT_TIMEOUT = 1, default_buffer = 1024, short_delay = 0.1, long_delay = 1):
        '''
        This function:
        Establishes a socket connection to the Signal Generator. Uses address (Including Port Number) as an argument.
        Performs a reset on the unit and sets the fixed frequency generator mode. 
        Sets the Display to On in Remote mode
        @params: 
            sigAddress          : sigHOST str, sigPORT int
            default_timeout     : int timeout for waiting to establish connection
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
            rx_str = self.requestSigGenData('*IDN?')   # Get instrument identification
            print(f'Connected to: {rx_str}')      # Display instrument identification
            self.sendSigGenCmd('*CLS')                 # Clear the output buffer                        
            self.sendSigGenCmd('*RST')                 # Reset unit
            self.sendSigGenCmd('SYST:DISP:UPD ON')
            time.sleep(short_delay)
        except Exception as e:
            print(e, f'Check to see if the port number is {SG_PORT}')

    def dumpSigGenData(self):
        '''
        This function receives and displays the data after a query command
        @params:
            None    
        '''
        while True:
            try:
                dump_str = self.recv(self.default_buffer)       # Receive data - 1024 bytes
                print(f'Dumping buffer data: {dump_str}')      # Display received data
            except socket.timeout:
                break

    def sendSigGenCmd(self, command_str):
        '''
        This function sends the command and adds \n at the end of any commands 
            sent to the test device
        @params:
            command  : string    
        '''
        self.sendall(bytes(command_str, encoding = 'utf8'))           # Send command to device, as bytes
        self.sendall(bytes('\n', encoding = 'utf8'))                  # Send end of line termination

    def requestSigGenData(self, request_str, response_buffer = 'default', timeout_max = 20):
        ''' Send request string

        This function requests and reads the command to and from the test device
        @params:
            command  : string    
        ''' 
        if type(response_buffer) == str:
            response_buffer = self.default_buffer
        self.dumpSigGenData()                                         # Cleanup the receive buffer
        self.sendSigGenCmd(request_str)                               # Send the request
        return_str = b''                                           # Initialize Rx buffer
        time_start = time.time()                                   # Get the start time
        while True:
            time.sleep(self.delay_short_s)                         # Introduce a short delay
            try:
                return_str += self.recv(response_buffer)           # Attempt to read the buffer
            except socket.timeout:
                if (time.time() - time_start) > timeout_max:
                       raise StopIteration('No data received from instrument') 
                else:
                    time.sleep(self.delay_short_s)                  # No response, keep waiting
            else:
                if return_str.endswith(b'\n'):                      # Test to see if end of line has been reached, i.e. all the data Rx
                    return return_str[:-1] 

    def setRFOut(self, rf_state):
        ''' Set RF State

        This function sets the RF Output ON or OFF
        @pa
        rams rf_state  : bool    [On/Off]
        '''
        self.sendSigGenCmd(f'OUTP {rf_state}')                         # Set RF Output
        dump_str = self.requestSigGenData('OUTP?')                     # Query RF Output
        if dump_str.decode('utf8') == '1':                          # Decode received data
            print('RF Output On')
        else: print('RF Output Off')

    def setSigGenPower(self, power):
        '''
        This function sets the power of the signal generator
        @params:
            power: float    [dBm]
        '''
        self.sendSigGenCmd(f'POW {power}')                             # Set the Power
        data = self.requestSigGenData('POW?')                          # Query the Power
        print(f'Sig gen power = {data.decode()} dBm')                        # Display received Power

    def setSigGenFreq(self, Freq):
        ''' Set frequency

        This function sets the fixed frequency of the signal generator
        @param  Freq: float [MHz]
        '''
        self.sendSigGenCmd(f'FREQ {Freq}')                             # Set frequency
        data = self.requestSigGenData('FREQ?')                         # Query frequency
        print(f'Sig gen frequency = {(float(data) / 1e6)} MHz')              # Display received frequency
        
    def sigGenFreqs(self):
        ''' Generate discreet frequencies

        This function generates discrete frequencies from 100 MHz
        to 2.3 GHz at 100 MHz steps
        @params:
            none
        '''
        self.sendSigGenCmd('FREQ:MODE FIX')                    # Set frequency mode to fixed
        cur_freq = 0                                        # Initialize freq container     
        for i in range(1, 24):                              # Offset to 1, freq cannot be 0 MHz
            time.sleep(2)                                   # Delay 3 secs for visibility
            cur_freq = (100 * i)                            # Compute and iterate frequency multiples
            cur_freq_str = str(cur_freq) + 'MHz'            # Convert frequency to string & add units
            self.sendSigGenCmd(f'FREQ {cur_freq_str}')         # Set frequency 
            print(f'Set Frequency to {cur_freq_str}...')    # Print current frequency
            print(i)

    def closeGenSock(self):
        self.setRFOut(OFF)
        self.close()                                        # Close connection socket
        print('Signal Generator socket Disconnected')

# ---------------------------------------------------
# End of Signal Generator class
# ---------------------------------------------------

#%%   
# Main program
# -----------------------
if __name__ == '__main__':
    print('/------Setup signal generator---------/')
    sigGen = sig_sock()                                 # Call main class
    sigGen.sig_gen_connect((SG_HOST, SG_PORT))           # Connect Sig Gen remotely
    time.sleep(1)                                       # Delay 1 sec
    sigGen.setSigGenPower(-30)                          # Sets Sig Gen power
    time.sleep(1)                                       # Delay 1 sec
    sigGen.setRFOut(ON)                                 # Activate Output signal                                
    time.sleep(1)                                       # Delay 1 sec
    sigGen.sigGenFreqs()                                # Activate frequency generator
    time.sleep(1)                                       # Delay 1 sec
    sigGen.closeGenSock()                               # Close socket
    print('/------End of Setup signal generator---------/')
