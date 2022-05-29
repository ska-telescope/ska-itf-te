#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: Monde 
@Date: 05-04-2022
@Affiliation: Test Engineer
@Functional Description: 
    1. This script generates a frequency sweep from 100 MHz to 2 GHz at 100 MHz steps
    2. The parameters can be adjusted as per user requirements
    3. Where it applies SG denotes Signal Generator 
    4. Run the script by parsing the following arguments on the terminal:
        - start frequency = 100000000 or 100e6, integer with no units [100 MHz]
        - stop frequency = 2000000000 or 2e9, integer with no units [2 GHz]
        - step frequency = 100000000 or 100e6, integer with no units [100 MHz]
        - dwell time = 1000, integer with no units [ms]
        - sweep mode = 'auto', string [auto/man]  
@Notes: 
    1. This script was written for the SMB100A Signal Generator. Raw ethernet socket communication is used
        and thus VISA library/installation is not required
    2. This script uses scpi protocol for the automatic test equipment intended

@modifier: Benjamin / Monde
@Date: 26-05-2022
    1. Moved the start and stop freq functions to the sweep func
    2. Tidy docstrings and formatting
    3. File renaming to sg_smb100a_generate_frequency_sweep_1.py
@Revision: 1
'''

import time
import socket
import argparse

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
# --------------------------------------------

class SG_SOCK(socket.socket):
    def initSigGen(self, SG_ADDRESS, DEFAULT_TIMEOUT = 1, default_buffer = 1024, short_delay = 0.1, long_delay = 1):
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
            rx_str = self.sg_requestdata('*IDN?')
            print(f'Connected to: {rx_str}')
            self.sg_sendcmd('*CLS')                                     
            self.sg_sendcmd('*RST')
            self.sg_sendcmd('SYST:DISP:UPD ON')
            time.sleep(short_delay)
        except Exception as e:
            print(e, f'Check to see if the port number is {SG_PORT}')

    def sg_dumpdata(self):
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

    def sg_sendcmd(self, command_str):
        ''' Send command.

        This function sends the command and adds \n at the end of any commands 
            sent to the test device
        @params: 
            command  : scpi string   
        '''
        self.sendall(bytes(command_str, encoding = 'utf8'))
        self.sendall(bytes('\n', encoding = 'utf8'))
        time.sleep(RESPONSE_TIMEOUT)

    def sg_requestdata(self, request_str, response_buffer = 'default', timeout_max = 20):
        ''' Request data.

        This function requests and reads the command to and from the test device
        @params:
            command  : scpi string  
        ''' 
        if type(response_buffer) == str:
            response_buffer = self.default_buffer
        self.sg_dumpdata()                                         # Cleanup the receive buffer
        self.sg_sendcmd(request_str)                           # Send the request
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
        self.sg_sendcmd(f'OUTP {rf_state}')  
        dump_str = self.sg_requestdata('OUTP?')
        if dump_str == b'1':   
            print('RF Output On')
        else: print('RF Output Off')

    def setSigGenPower(self, power):
        ''' Set power.

        This function sets the power of the signal generator
        @params:
            power   : power level in dBm (default = -10)
        '''
        self.sg_sendcmd(f'POW {power}')
        data = self.sg_requestdata('POW?')
        print(f'Sig gen power = {data.decode()} dBm')
        
    def setSigGenSweep(self, freq_start, freq_stop, freq_step, dwel_time):
        ''' Generate sweep.

        This function sets the sweep frequency of the signal generator
        at 100MHz step
        @params:
            freq_start      : start frequency in Hz (not less than 9 kHz)
            freq_stop       : stop frequency in Hz (not more than 6 GHz)
            freq_step       : step frequency in Hz (default = 100 MHz)
            dwel_time       : duration of frequency output in ms (default=1000 ms)
            sweep_mode      : sweep mode (auto / manual)
        ''' 
        # start frequency acquisition
        self.sg_sendcmd(f'SOUR:FREQ:STAR {freq_start}')
        time.sleep(RESPONSE_TIMEOUT)
        self.sg_sendcmd('FREQ:STAR?')
        time.sleep(RESPONSE_TIMEOUT)
        data = float(self.recv(1024))
        print(f'Sig gen start frequency = {(data / 1e6)} MHz')
        freq_start = data
        # end of start frequency acquisition

        # stop frequency acquisition
        self.sg_sendcmd(f'SOUR:FREQ:STOP {freq_stop}')
        time.sleep(RESPONSE_TIMEOUT)
        self.sg_sendcmd('FREQ:STOP?')
        data = float(self.recv(1024))
        time.sleep(RESPONSE_TIMEOUT)
        print(f'Sig gen stop frequency = {(data / 1e6)} MHz')
        freq_stop = data 
        # end of stop frequency acquisition 

         # Step frequency acquisition - return from args.str to int
        self.sg_sendcmd(f'SOUR:FREQ:STEP {freq_step}')
        self.sg_sendcmd('FREQ:STEP?')
        time.sleep(RESPONSE_TIMEOUT)
        data = float(self.recv(1024))
        freq_step = data
        # End of step frequency acquisition

        centFreq = (freq_start + freq_stop) / 2
        span = freq_stop - freq_start    
        # 1. Set the sweep range
        self.sg_sendcmd(f'FREQ:CENT {centFreq} Hz')
        self.sg_sendcmd(f'FREQ:SPAN {span} Hz')
        # 2. Select linear or logarithmic spacing
        self.sg_sendcmd('SWE:FREQ:SPAC LIN')
        # 3. Set the step width and dwell time
        self.sg_sendcmd(f'SWE:FREQ:STEP:LIN {freq_step} Hz')
        self.sg_sendcmd(f'SWE:FREQ:DWEL {dwel_time} ms')
        # 4. Select the trigger mode
        self.sg_sendcmd('TRIG:FSW:SOUR SING')
        # 5. Select sweep mode and activate the sweep
        self.sg_sendcmd(f'SWE:FREQ:MODE AUTO')
        self.sg_sendcmd('FREQ:MODE SWE')
        # 6. Trigger the sweep     
        self.sg_sendcmd('SOUR:SWE:FREQ:EXEC')
        print('Executing sweep...')

    def closeGenSock(self):
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
    parser.add_argument('freq_start', type = str, help = 'the start frequency incl. units (Hz)')
    parser.add_argument('freq_stop', type = str, help = 'the stop frequency incl. units (Hz)')
    parser.add_argument('freq_step', type = str, help = 'the step frequency incl. units (Hz)')
    parser.add_argument('dwel_time', type = int, help = 'the sweep dwell time (ms)')
    args = parser.parse_args()