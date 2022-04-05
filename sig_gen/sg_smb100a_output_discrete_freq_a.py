#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
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
    5. Where it applies SG denotes Signal Generator   
@Revision: A

@modifier: Monde
@Functional Description:
    Added arguments parser for power, start freq, stop freq and step freq.
    Cleaned
@Date: 03-04-2022 
"""

import time
import socket
import argparse

from sg_smb100a_set_freq_power_rf_1 import ON

# -----------------Connection Settings----------------------
SG_PORT = 5025                      # default SMB R&S port 
SG_HOST = '10.8.88.166'             # smb100a signal generator IP
SG_ADDRESS = (SG_PORT, SG_HOST)
#-----------------------------------------------------------
# ----------------Initialization of Variables---------------    
DEFAULT_TIMEOUT = 1        # Default socket timeout
rf_state = 0               # Default RF Out state
# ---------------------------------------------------------
# --------------Global Variables---------------------------
dump_str = ''

class sig_sock(socket.socket):
    def sig_gen_connect(self,sigAddress,DEFAULT_TIMEOUT = 1,default_buffer = 1024,short_delay = 0.1,long_delay = 1):
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
            rx_str = self.sg_requestdata('*IDN?')   # Get instrument identification
            print('Connected to: %s'%rx_str)        
            self.sg_sendcmd('*CLS')                                      
            self.sg_sendcmd('*RST')                 
            self.sg_sendcmd('SYST:DISP:UPD ON')
            time.sleep(short_delay)
        except Exception as e:
            print(e,f"Check to see if the port number is {SG_PORT}")

    def sa_dumpdata(self):
        """
        This function receives and displays the data after a query command
        @params command  : string    
        """
        while True:
            try:
                dump_str = self.recv(self.default_buffer)       # Receive data - 1024 bytes
                print('Dumping buffer data: %s'%dump_str)       # Display received data
            except socket.timeout:
                break

    def sg_sendcmd(self,command_str):
        """
        This function sends the command and adds \n at the end of any commands 
            sent to the test device
        @params command  : scpi string    
        """
        self.sendall(bytes(command_str, encoding='utf8'))           
        self.sendall(bytes('\n', encoding='utf8'))                   

    def sg_requestdata(self,request_str,response_buffer = 'default',timeout_max = 20):
        """
        This function requests and reads the command to and from the test device
        @params 
            command  : scpi string    
        """ 
        if type(response_buffer) == str:
            response_buffer = self.default_buffer
        self.sa_dumpdata()                                         
        self.sg_sendcmd(request_str)                               
        return_str = b''                                           
        time_start = time.time()                                   
        while True:
            time.sleep(self.delay_short_s)                         
            try:
                return_str += self.recv(response_buffer)           
            except socket.timeout:
                if (time.time()-time_start) > timeout_max:
                       raise StopIteration('No data received from instrument') 
                else:
                    time.sleep(self.delay_short_s)                  # No response, keep waiting
            else:
                if return_str.endswith(b'\n'):                      # Test to see if end of line has been reached, i.e. all the data Rx
                    return return_str[:-1] 

    def setSigGenRF(self, rf_state = ON):
        """
        This function sets and returns the RF Status
            @params:
                rf_state  : Sig gen RF output as On or Off
            @returns:
                rf_state  : Sig gen RF status as On or Off
        """
        self.sg_sendcmd(f'OUTP {rf_state}')                         
        dump_str = self.sg_requestdata('OUTP?')                     
        print(f'dump_str is {dump_str}')                             
        if dump_str.decode('utf8')=='1\n':                          
            print("RF Output On")
        else: print("RF Output Off")

    def setSigGenPower(self, power = -10):
        """
        This function sets the power of the signal generator
        @params:
            power           : power level in dBm (default = -10)
        """
        self.sg_sendcmd(f'POW {power}')                             
        data = self.sg_requestdata('POW?')                         
        print(f"Sig gen power = {data} dBm")                        

    def setSigGenStartFreq(self,freq_start=100e6):
        """
        This function sets the start frequency of the signal generator
        @params:  
            freq_start         : start frequency in Hz (not less than 9 kHz)
        """
        self.sg_sendcmd(f'FREQ {freq_start}')                 
        data = int(self.sg_requestdata('FREQ?'))             
        print(f"Sig Gen START frequency = {(data/1e6)} MHz") 
        return freq_start 

    def setSigGenStopFreq(self,freq_stop):
        """
        This function sets the stop frequency of the signal generator
        @params:  
            freq_stop         : stop frequency in Hz (not more than 6 GHz)
        """
        self.sg_sendcmd(f'FREQ {freq_stop}')                          
        data = int(self.sg_requestdata('FREQ?'))                      
        print(f"Sig Gen STOP frequency = {(data/1e6)} MHz")          
        return freq_stop             
        
    def setSigGenDscrtFreqs(self, freq_start,freq_stop,freq_step):
        """
        This function generates discrete frequencies from start freq
        to stop freq at a required step freq
        @params: 
                freq_start     : start frequency in Hz (not less than 9 kHz)
                freq_stop      : stop frequency in Hz (not more than 6 GHz)
                freq_step      : step frequency in Hz (default = 100 MHz)
        """

        self.sg_sendcmd('FREQ:MODE FIX')                    
        cur_freq = 0                                            
        i = 0
        while cur_freq <= freq_stop:
            time.sleep(1)
            cur_freq = freq_start + (freq_step*i)
            cur_freq_str = str(cur_freq) + ' Hz'            
            self.sg_sendcmd(f'FREQ {cur_freq_str}')        
            i=i+1
            data = int(self.sg_requestdata('FREQ?'))       
            print(f"Sig gen frequency = {(data/1e6)} MHz")                         

    def closeGenSock(self):
        self.close()                                        # Close connection socket
        print('Signal Generator socket Disconnected')

# ---------------------------------------------------
# End of Signal Generator class
# ---------------------------------------------------

#----------------------------------------------------   
# Main program
# ---------------------------------------------------
if __name__ == '__main__':
    # Set up arguments to be parsed 
    parser = argparse.ArgumentParser(description = "Specify Sig Gen Start Freq, Stop Freq, Step Freq and Power")
    parser.add_argument("power", type=int, help="the power level (dBm)")
    parser.add_argument("freq_start", type=float, help="the start frequency (Hz)")
    parser.add_argument("freq_stop", type=float, help="the stop frequency (Hz)")
    parser.add_argument("freq_step", type=float, help="the step frequency (Hz)")
    args = parser.parse_args()

    print("/------Setup signal generator---------/")
    # Initialise the signal generator to a known state
    sigGen = sig_sock()              
        # Connect Sig Gen remotely
    sigGen.sig_gen_connect((SG_PORT,SG_HOST))    
        # Set up sig gen to specified power
    sigGen.setSigGenPower(args.power)         
        # Set up sig gen to specified start freq
    sigGen.setSigGenStartFreq(args.freq_start)
        # Set up sig gen to specified start freq
    sigGen.setSigGenStopFreq(args.freq_stop)
        # Set RF on or off
    sigGen.setSigGenRF('On')         
        # Set up sig gen to specified step freq and generate discrete frequencies
    sigGen.setSigGenDscrtFreqs(args.freq_start, args.freq_stop, args.freq_step)
        # Close socket to SG
    sigGen.closeGenSock()                                                   # Close socket
    print("/------End of Setup signal generator---------/")
