#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Vhuli and Monde 
@Date: 22-08-2022
@Affiliation: Test Engineers
@Functional Description: 
    1. This script reads the noise power density of the NC1113B noise source in dBm/Hz at different RBWs
    and plots power vs. frequency
    2. Run the script by parsing the following arguments on the terminal:
        - start frequency = 0 or 100e6, integer with no units [0 Hz]
        - stop frequency = 2000000000 or 3e9, integer with no units [3 GHz]
        - resolution bandwidth = 3000000 or 3e6, integer with no units [3 MHz]
        - video bandwidth = 3000000 or 3e6, integer with no units [3 MHz]
 
@Notes: 
    1. This script was written for the FSH8 Spectrum Analyzer. 
        Raw ethernet socket communication is used and thus VISA library/installation is not required
    2. This script uses scpi protocol for the automatic test equipment intended

@Revision: 1
"""

#-------------------------- IMPORT REQUIRED PACKAGES-------------------------------------

import socket
import time
from numpy import double

# -------------------------- CONNECTION SETTINGS -------------------------------------------
SA_HOST = '10.8.88.138'         # fsh8 spectrum analyzer IP
SA_PORT = 5555                  # fsh8 spectrum analyzer port
SA_ADDRESS = (SA_HOST, SA_PORT)
#-------------------------- CONSTANTS--------------------------

FREQ_STEP = 3015873             # step frequency in MHz
DEFAULT_TIMEOUT = 1             # Default socket timeout
RECDUR = 5                      # Time in seconds to find maxhold peaks
RESPONSE_TIMEOUT = 0.01
# ----------------Initialization of Variables---------------    
power_values = []
pow_values = []
freq_values = []
ampl_vals = []
freq_vals = []
#-------------------------SPECTRUM ANALYZER SOCKET CLASS----------------------------------
class SA_SOCK(socket.socket):
    def connectSpecAna(self, SA_ADDRESS, default_timeout = 1, default_buffer = 1024, short_delay = 0.1, long_delay = 1):
        ''' Establish socket connect connection.

        This function:
            - Establishes a socket connection to the Signal Generator. Uses address (Including Port Number) as an argument.
            - Performs a reset on the unit and sets the fixed frequency generator mode. 
            - Sets the Display to On in Remote mode
        @params 
        specAddress         : specHOST str, specPORT int
        default_timeout     : int timeout for waiting to establish connection
        long_delay          : int time delay 1000 ms
        short_delay         : int time delay 100 ms
        default_buffer      : int 1024 bytes
        '''    
        self.connect(SA_ADDRESS)  # connect to spectrum analyzer via socket at IP '10.8.88.138' and Port 5555
        self.settimeout(default_timeout) 
        self.delay_long_s = long_delay
        self.delay_short_s = short_delay
        self.default_buffer = default_buffer

        rx_str = self.requestSpecAnaData('*IDN?') # requesting instrument identity and print 
        print(f'Connected to: {rx_str}')
        self.sendSpecAnaCmd('*CLS')     
        self.sendSpecAnaCmd('*RST')                 # instrument reset
        self.sendSpecAnaCmd('INST:SEL SAN')         # spectrum analyzer mode
        self.sendSpecAnaCmd('SYST:DISP:UPD ON')    
        time.sleep(short_delay)

    def dumpSpecAnaData(self):
        ''' Receive string

        This function receives and displays the data after a query command
        @params:
            None
        '''   
        while True:
            try:
                dump_str = self.recv(self.default_buffer)
                print(f'Dumping buffer data: {dump_str}')
            except socket.timeout:
                break

    def sendSpecAnaCmd(self, command_str):
        ''' Send command
        
        This function sends the command and adds \n at the end of any commands 
        sent to the test device
        @params:
            command_str  : string    
        '''
        self.sendall(bytes(command_str, encoding = 'utf8') + b'\n')
        time.sleep(RESPONSE_TIMEOUT)
                
    def requestSpecAnaData(self, request_str, response_buffer = 'default', timeout_max = 10):
        ''' Request data

        This function requests and reads the command to and from the test device
        @params:
            request_str  : string
        ''' 
        if type(response_buffer) == str:
            response_buffer = self.default_buffer
        #self.sa_dumpdata()                                         # Cleanup the receive buffer
        self.sendSpecAnaCmd(request_str)                           # Send the request
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
                    time.sleep(self.delay_short_s)                  # No response, keep waiting
            else:
                if return_str.endswith(b'\n'):                      # Test to see if end of line has been reached, i.e. all the data Rx
                    return return_str[:-1]                         # Return string

    def setSpecAnaSweep(self, start_f = 0, stop_f = 100e6, nr_points = 625):
        ''' Setup sweep

        This function sets up the Spectrum Analyser Sweep parameters
        @params:
                start_f FLOAT: Start frequency [MHz] 
                stop_f FLOAT: Stop frequency [MHz] 
                nr_points INTEGER:        
        '''
        self.sendSpecAnaCmd(f'FREQ:STAR {start_f} Hz')
        self.sendSpecAnaCmd(f'FREQ:STOP {stop_f} Hz')
        self.sendSpecAnaCmd(f'SWE:POIN {nr_points}')
        start_f_set = double(self.requestSpecAnaData('FREQ:STAR?'))
        stop_f_set = double(self.requestSpecAnaData('FREQ:STOP?'))
        nr_points_set = int(self.requestSpecAnaData('SWE:POIN?'))
        print(f'SA Start Freq: {start_f_set * 1e-6} MHz, Stop Freq: {stop_f_set * 1e-6} MHz, Points: {nr_points_set}')      
        return start_f_set, stop_f_set, nr_points_set #Returns the values reported by the SA
        
    def setSpecAnaBandwidth(self, rbw_auto = 'on', rbw = 0, vbw_auto = 'on', vbw = 0):
        ''' Set resolution and video bandwidths

        This function sets the resolution and video bandwidth
        @param:
            rbw_auto   : Set RBW auto 'on' or 'off' : 'on'|'off'
            rbw        : Sets the RBW in Hz for rbw_auto == 'on'
            vbw_auto   : Set VBW auto 'on' or 'off' : 'on'|'off'
            vbw        : Sets the VBW in Hz for vbw_auto == 'on'
        '''
        if rbw_auto.upper() in ('ON', 'OFF'):
            self.sendSpecAnaCmd(f'BAND:AUTO {rbw_auto.upper()}')
            rbw_auto_set = int(self.requestSpecAnaData('BAND:AUTO?'))
            if rbw_auto.upper() == 'OFF':
                self.sendSpecAnaCmd(f'BAND {rbw}')
                rbw_set = double(self.requestSpecAnaData('BAND?'))
            else:
                rbw_set = 0.0
                
        if vbw_auto.upper() in ('ON', 'OFF'):
            self.sendSpecAnaCmd(f'BAND:VID:AUTO {vbw_auto.upper()}')
            vbw_auto_set = int(self.requestSpecAnaData('BAND:VID:AUTO?'))
            if vbw_auto.upper() == 'OFF':
                self.sendSpecAnaCmd(f'BAND:VID {vbw}')
                vbw_set = double(self.requestSpecAnaData('BAND:VID?'))
            else:
                vbw_set = 0.0    
                
        print(f'SA RBW set to AUTO {rbw_auto_set}, RBW = {round((rbw_set * 1e-3), 2)} kHz')
        print(f'SA VBW set to AUTO {vbw_auto_set}, VBW = {round((vbw_set * 1e-3), 2)} kHz')
    
    
    def setSpecAnaDetector(self, det_mode = 'rms'):
        ''' Set Detector Mode

        This function sets the detector mode of the Spectrum analyzer
        @param:
            det_mode   : Sets the detector mode     : 'APE' (Autopeak)|'POS'|'NEG'|'SAMP'|'RMS'|'AVER'|'QPE' (Quasipeak)
            trace_mode : Sets the trace mode        : 'WRIT' (Clear/Write)|'MAXH'|'AVER'|'VIEW'
        '''
        self.sendSpecAnaCmd(f'DET {det_mode.upper()}')
        det_mode_set = self.requestSpecAnaData('DET?')
        trace_mode_set = self.requestSpecAnaData('DISP:WIND:TRAC:MODE?')
        print(f'SA trace mode set to = {trace_mode_set.decode()}')
        return print(f'SA detector mode set to = {det_mode_set.decode()}')
        
    def setSpecAnaAmplitude(self, ref_level_dBm = 0, att_level_dB = 5):
        ''' Method that sets the amplitude parameters for the spectrum analyzer and sets the attenuator
        ref_level_dBm    : Sets the reference level [dBm]'''
     
        self.sendSpecAnaCmd('INP:ATT:AUTO OFF')
        self.sendSpecAnaCmd(f'DISP:WIND:TRAC:Y:RLEV {ref_level_dBm}dBm')

        self.sendSpecAnaCmd(f'INP:ATT {att_level_dB} dB')
        ref_level_dBm_set = double(self.requestSpecAnaData('DISP:WIND:TRAC:Y:RLEV?'))
        att_level_dB_set = double(self.requestSpecAnaData('INP:ATT?'))
        print(f'SA amplitude reference level set to REF {ref_level_dBm_set} dBm')
        print(f'SA input attenuator set to {att_level_dB_set} dB')
        
    def getSpecAnaSweepData(self, maximum_wait_time_s = 10 * 60):
        ''' Method that starts a new sweep and downloads the data, returned as a list
        Returns a list of the measured data in [dBm]
        '''
        self.sa_dumpdata()
        self.sendSpecAnaCmd('INIT1:CONT OFF')
        self.sendSpecAnaCmd('INIT1')
        rx_str = self.requestSpecAnaData('*OPC?', 'default', maximum_wait_time_s)
        return list(eval(self.requestSpecAnaData('TRACE1? TRACE1')))

    def setSpecAnaSweepTime(self, sweep_time):
        self.sendSpecAnaCmd(f'SWE:TIME {sweep_time}')
        return sweep_time

    def setMarkerFunction(self, marker_freq):
        self.sendSpecAnaCmd(f'CALC:MARK ON')
        self.sendSpecAnaCmd(f'CALC:MARK:FUNC:NOIS ON')
        self.sendSpecAnaCmd(f'CALC:MARK:X {marker_freq}')


    def getSpecAnaTraceParams(self, freq_start, freq_stop): 
        ''' Read trace data
        
        This function reads the power trace data and calculates the 
        trace frequency points

        @params:
            freq_start      : start frequency in Hz
            freq_stop       : stop frequency in Hz
        '''                                                    
        self.sendSpecAnaCmd('FORM:DATA ASC')                     
        power_data = self.requestSpecAnaData('TRAC:DATA? TRACE1')
        power_data = power_data.decode()
        power_data = str(power_data)
        power_data = power_data.split(',') 
        No_of_Sweep_Points = int(self.requestSpecAnaData('SWE:POIN?'))
        print(f'No of Sweep Points = {No_of_Sweep_Points}')
        
        for s in power_data:
            power_data_flo = round(float(s), 2) 
            power_values.append(power_data_flo)
            
        pow_val_len = 0
        while pow_val_len < No_of_Sweep_Points:
            pow_values.append(power_values[pow_val_len])
            pow_val_len += 1

        freq_step_size = int((float(freq_stop) - float(freq_start)) / (No_of_Sweep_Points - 1))
        for i in range(0, No_of_Sweep_Points, 1):
            freq_values.append(float(freq_start) + (i * freq_step_size))
        return freq_values, pow_values    

    def closeSpecAna(self):
        self.close()

