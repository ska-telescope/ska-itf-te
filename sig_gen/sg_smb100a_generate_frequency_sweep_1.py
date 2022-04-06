#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Monde 
@Date: 05-04-2022
@Affiliation: Test Engineer
@Functional Description: 
    1. This script generates a frequency sweep from 100 MHz to 2 GHz at 100 MHz steps
    2. The parameters can be adjusted as per user requirements
    3. Where it applies SG denotes Signal Generator 
    4. Run the script by parsing the following arguments on the terminal:
        - start frequency = 100000000, integer with no units [100 MHz]
        - stop frequency = 2000000000, integer with no units [2 GHz]
        - step frequency = 100000000, integer with no units [100 MHz]
        - sweep mode = 'auto', string [auto/man]  
@Notes: 
    1. This script was written for the SMB100A Signal Generator. Raw ethernet socket communication is used
        and thus VISA library/installation is not required
    2. This script uses scpi protocol for the automatic test equipment intended

@Revision: A

"""

import time
import socket
import argparse
import math

# -----------------Connection Settings----------------------
SG_PORT = 5025                      # default SMB R&S port 
SG_HOST = '10.8.88.166'             # smb100a signal generator IP
SG_ADDRESS = (SG_PORT, SG_HOST)
#-----------------------------------------------------------
# ----------------Initialization of Variables---------------    
DEFAULT_TIMEOUT = 1        # Default socket timeout
RF_OFF = 0
RF_ON = 1

dump_str = ''

# --------------------------------------------


class SG_SOCK(socket.socket):
    def initSigGen(self,sigAddress,DEFAULT_TIMEOUT = 1,default_buffer = 1024,short_delay = 0.1,long_delay = 1):
        """

                This function:
                    Establishes a socket connection to the Signal Generator. Uses address (Including Port Number) as an argument.
                    Performs a reset on the unit and sets the fixed frequency generator mode. 
                    Sets the Display to On in Remote mode
                @params 
                    sigAddress          :   sigHOST str IP address of the device
                                            sigPORT int port number to device access
                    default_timeout     : int [Optional] Timeout for waiting to establish connection
                    long_delay          : int
                    short_delay         : int
                    default_buffer      : int

        """
        try:
            self.connect(sigAddress)                                
            self.settimeout(DEFAULT_TIMEOUT)
            self.delay_long_s = long_delay
            self.delay_short_s = short_delay
            self.default_buffer = default_buffer
            rx_str = self.sa_requestdata('*IDN?')
            print('Connected to: %s'%rx_str)
            self.sa_sendcmd('*CLS')                                     
            self.sa_sendcmd('*RST')
            self.sa_sendcmd('SYST:DISP:UPD ON')
            time.sleep(short_delay)
        except Exception as e:
            print(e,f"Check to see if the port number is {SG_PORT}")

    def sa_dumpdata(self):
        """
        This function receives and displays the data after a query command
        @params: 
            command  : string    
        """
        while True:
            try:
                dump_str = self.recv(self.default_buffer)
                print('Dumping buffer data: %s'%dump_str)
            except socket.timeout:
                break

    def sa_sendcmd(self,command_str):
        """

        This function sends the command and adds \n at the end of any commands 
            sent to the test device
        @params: 
            command  : scpi string   

        """
        self.sendall(bytes(command_str, encoding='utf8'))
        self.sendall(bytes('\n', encoding='utf8'))

    def sa_requestdata(self,request_str,response_buffer = 'default',timeout_max = 20):
        """

        This function requests and reads the command to and from the test device
        @params:
            command  : scpi string  
              
        """ 
        if type(response_buffer) == str:
            response_buffer = self.default_buffer
        self.sa_dumpdata()                                         # Cleanup the receive buffer
        self.sa_sendcmd(request_str)                           # Send the request
        return_str = b''                                            # Initialize Rx buffer
        time_start = time.time()                                   # Get the start time
        while True:
            time.sleep(self.delay_short_s)                         # Introduce a short delay
            try:
                return_str += self.recv(response_buffer)           # Attempt to read the buffer
            except socket.timeout:
                if (time.time()-time_start) > timeout_max:
                       raise StopIteration('No data received from instrument') 
                else:
                    time.sleep(self.delay_short_s)                
            else:
                if return_str.endswith(b'\n'):                  
                    return return_str[:-1] 

    def setSigGenRF(self, rf_state = RF_ON):
        """
        This function sets and returns the RF Status
            @params:
                rf_state  : Sig gen RF output as On or Off
            @returns:
                rf_state  : Sig gen RF status as On or Off
        """
        self.sa_sendcmd(f'OUTP {rf_state}')  
        dump_str = self.sa_requestdata('OUTP?')
        time.sleep(1)
        if dump_str==b'1': 
            time.sleep(1)      
            print("RF Output On")
        else: print("RF Output Off")

    def setSigGenPower(self, power):
        """
        This function sets the power of the signal generator
        @params:
            power   : power level in dBm (default = -10)
        """
        self.sa_sendcmd(f'POW {power}')
        data = self.sa_requestdata('POW?')
        print(f"Sig gen power = {data.decode()} dBm")
        
    def setSigGenStartFreq(self, freq_start):
        """
        This function sets the start frequency of the signal generator
        @params:  
            freq_start         : start frequency in Hz (not less than 9 kHz)
        """
        self.sa_sendcmd(f'SOUR:FREQ:STAR {freq_start}Hz')
        time.sleep(5)
        self.sa_sendcmd('FREQ:STAR?')
        data = float(self.recv(1024))
        print(f"Sig gen start frequency = {(data/1e6)} MHz")
        return freq_start

    def setSigGenStopFreq(self, freq_stop):
        """
        This function sets the stop frequency of the signal generator
        @params:  
            freq_stop         : stop frequency in Hz (not more than 6 GHz)
        """
        self.sa_sendcmd(f'SOUR:FREQ:STOP {freq_stop}Hz')
        time.sleep(5)
        self.sa_sendcmd('FREQ:STOP?')
        data = float(self.recv(1024))
        print(f"Sig gen stop frequency = {(data/1e6)} MHz")
        return freq_stop

    def setSigGenSweep(self, freq_start, freq_stop, freq_step, dwel_time, sweep_mode):
        """
        This function sets the sweep frequency of the signal generator
        at 100MHz step
        @params:
            freq_start      : start frequency in Hz (not less than 9 kHz)
            freq_stop       : stop frequency in Hz (not more than 6 GHz)
            freq_step       : step frequency in Hz (default = 100 MHz)
            dwel_time       : duration of frequency output in ms (default=1000 ms)
            sweep_mode      : sweep mode (auto / manual)
        """   
        centFreq = (freq_start+freq_stop)/2
        time.sleep(1)
        span = freq_stop-freq_start    
        time.sleep(1)
        # 1. Set the sweep range
        self.sa_sendcmd(f'FREQ:CENT {centFreq} Hz')
        time.sleep(1)
        self.sa_sendcmd(f'FREQ:SPAN {span} Hz')
        time.sleep(1)
        # 2. Select linear or logarithmic spacing
        self.sa_sendcmd('SWE:FREQ:SPAC LIN')
        time.sleep(1)
        # 3. Set the step width and dwell time
        self.sa_sendcmd(f'SWE:FREQ:STEP:LIN {freq_step} Hz')
        time.sleep(1)
        self.sa_sendcmd(f'SWE:FREQ:DWEL {dwel_time} ms')
        time.sleep(1)
        # 4. Select the trigger mode
        self.sa_sendcmd('TRIG:FSW:SOUR SING')
        time.sleep(1)
        # 5. Select sweep mode and activate the sweep
        self.sa_sendcmd(f'SWE:FREQ:MODE {sweep_mode}')
        time.sleep(1)
        self.sa_sendcmd('FREQ:MODE SWE')
        # 6. Trigger the sweep
        self.sa_sendcmd('SOUR:SWE:FREQ:EXEC')
        print("Executing sweep...")

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
    parser = argparse.ArgumentParser(description = "Specify Sig Gen Start Frequency, Stop Frequency, Step Frequency, Dwell Time and Sweep Mode")
    parser.add_argument("freq_start", type=int, help="the start frequency incl. units (Hz)")
    parser.add_argument("freq_stop", type=int, help="the stop frequency incl. units (Hz)")
    parser.add_argument("freq_step", type=int, help="the step frequency incl. units (Hz)")
    parser.add_argument("dwel_time", type=int, help="the sweep dwell time (ms)")
    parser.add_argument("sweep_mode", type=str, help="the sweep mode (auto/man)")
    args = parser.parse_args()

    print("/------Setup signal generator---------/")
    sigGen = SG_SOCK()                        
    # Initiaslise the signal generator to a known state
    sigGen.initSigGen((SG_HOST,SG_PORT))    
    time.sleep(1)
    sigGen.setSigGenRF(RF_ON)
    time.sleep(1)
    sigGen.setSigGenPower(-30)                              
    time.sleep(1)
    sigGen.setSigGenStartFreq(args.freq_start)
    time.sleep(1)
    sigGen.setSigGenStopFreq(args.freq_stop)
    time.sleep(1)
    # Set up sig gen to start freq, stop freq, step freq, dwell time and sweep mode
    sigGen.setSigGenSweep(args.freq_start, args.freq_stop, args.freq_step, args.dwel_time, args.sweep_mode)  # Sets the freq sweep of the Sig Gen
    print("/------End of Setup signal generator---------/")
