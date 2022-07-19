#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Vhuli and Monde 
@Date: 20-05-2022
@Affiliation: Test Engineers
@Functional Description: 
    1. This script reads the power of the channel in dBm
    2. The parameters can be adjusted as per user requirements
    3. Run the script by parsing the following arguments on the terminal:
        - freq_start: the start frequency of the channel in Hz e.g. 100000000 or 100e6, integer with no units [100 MHz]
        - freq_stop: the stop frequency of the channel in Hz e.g. 2000000000 or 2e9, integer with no units [2 GHz]
        - chann_bw: the bandwidth of the channel in Hz e.g. 3000000 or 3e6, integer with no units [3 MHz]
        - chann_mode: the channel mode e.g. 'CLR' for Clear/Write, 'MAX' for Max Hold, string with ''
        - pow_unit, the unit of the channel power e.g. 'DBM' | 'DBMV' | 'DBUV' | 'VOLT' | 'WATT' | 'V' | 'W', string with ''

@Notes: 
    1. This script was written for the FSH8 Spectrum Analyzer. 
        Raw ethernet socket communication is used and thus VISA library/installation is not required
    2. This script uses scpi protocol for the automatic test equipment intended

@Revision: 1
"""

#-------------------------- IMPORT REQUIRED PACKAGES-------------------------------------
import socket
import time
import math
from numpy import double
import argparse
# --------------------------CONNECTION SETTINGS-------------------------------------------
SA_HOST = '10.8.88.138'         # fsh8 spectrum analyzer IP
SA_PORT = 5555                  # fsh8 spectrum analyzer port 18? 23?
SA_ADDRESS = (SA_HOST, SA_PORT)

# ----------------CONSTANTS---------------    
NUMPOINTS = 631                 # Number of measurement points (Max=625)
RBW = 10e3                       # Resolution BW of spectrum analyser
VBW = 300e3                     # Video BW of spectrum analyser
DEFAULT_TIMEOUT = 1             # Default socket timeout
RESPONSE_TIMEOUT = 0.01

#%%  

#-------------------------SPECTRUM ANALYZER SOCKET CLASS----------------------------------
class SA_SOCK(socket.socket):
    def connectSpecAna(self, address, default_timeout = 1, default_buffer = 1024, short_delay = 0.1, long_delay = 1):
        ''' Establish socket connect connection.

        This function:
            - Establishes a socket connection to the spectrum analyzer. Uses address (Including Port Number) as an argument.
            - Performs a reset on the unit and sets the measurement mode to spectrum analyzer mode. 
            - Sets the Display to On in Remote mode
        @params: 
        specAddress         : specHOST str, specPORT int
        default_timeout     : int timeout for waiting to establish connection
        long_delay          : int
        short_delay         : int
        default_buffer      : int
        '''    
        self.connect(address)  # connect to spectrum analyzer via socket at IP '10.8.88.138' and Port 5555
        # Mandatory timer and buffer setup.
        self.settimeout(default_timeout) 
        self.delay_long_s = long_delay
        self.delay_short_s = short_delay
        self.default_buffer = default_buffer

        rx_str = self.requestSpecAnaData('*IDN?') # requesting instrument identity and print 
        print(f'Connected to: {rx_str}')
        self.sendSpecAnaCmd('*CLS')                                     
        self.sendSpecAnaCmd('*RST')                 # instrument reset.
        self.sendSpecAnaCmd('INST:SEL SAN')         # spectrum analyzer mode
        self.sendSpecAnaCmd('SYST:DISP:UPD ON')
        time.sleep(short_delay)
       
    def dumpSpecAnaData(self):
        ''' Receive string

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

    def sendSpecAnaCmd(self, command_str):
        ''' Send command
        
        This function sends the command and adds \n at the end of any commands 
        sent to the test device
        @params:
            command_str  : string    
        '''
        self.sendall(bytes(command_str, encoding = 'utf8') + b'\n')
        time.sleep(RESPONSE_TIMEOUT)

    def requestSpecAnaData(self, request_str, response_buffer = 'default',timeout_max = 10):
        ''' Request data

        This function requests and reads the command to and from the test device
        @params:
            request_str  : string
        ''' 
        if type(response_buffer) == str:
            response_buffer = self.default_buffer
        self.dumpSpecAnaData()                                         # Cleanup the receive buffer
        self.sendSpecAnaCmd(request_str)                                # Send the request
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
        @params:
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
                
        if vbw_auto.upper() in ('ON','OFF'):
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
        ''' Set amplitude

        This function sets the amplitude parameters for the spectrum analyzer and sets the attenuator
        @param:
            ref_level_dBm    : Sets the reference level [dBm]
        '''
        self.sendSpecAnaCmd('INP:ATT:AUTO OFF')
        self.sendSpecAnaCmd(f'DISP:WIND:TRAC:Y:RLEV {ref_level_dBm}dBm')

        self.sendSpecAnaCmd(f'INP:ATT {att_level_dB} dB')
        ref_level_dBm_set = double(self.requestSpecAnaData('DISP:WIND:TRAC:Y:RLEV?'))
        att_level_dB_set = double(self.requestSpecAnaData('INP:ATT?'))
        print(f'SA amplitude reference level set to REF {ref_level_dBm_set} dBm')
        print(f'SA input attenuator set to {att_level_dB_set} dB')
        
    def getSpecAnaSweepData(self, maximum_wait_time_s = 10 * 60):
        ''' Get sweep

        This function starts a new sweep and downloads the data, returned as a list
        @return: a list of the measured data in [dBm]
        '''
        self.dumpSpecAnaData()
        self.sendSpecAnaCmd('INIT1:CONT OFF')
        self.sendSpecAnaCmd('INIT1')
        rx_str = self.requestSpecAnaData('*OPC?', 'default', maximum_wait_time_s)
        print(f'Operation Complete = {rx_str} dB')
        return list(eval(self.requestSpecAnaData('TRACE1? TRACE1')))

    def configSpecAnaPow(self, chann_bw, chann_mode, pow_unit):
        '''Set channel bandwidth, channel power mode and power unit

        This function sets the channel bandwidth for power measurement
        @params: 
            chann_bw    : Sets the channel bandwidth [Hz]
            chann_mode  : Sets the reference level [dBm]
            pow_unit    : Sets the reference level [dBm]  
        '''
        self.setSpecAnaDetector('rms')
        self.sendSpecAnaCmd(f'CALC:MARK:FUNC:CPOW:BAND {chann_bw} Hz')
        self.sendSpecAnaCmd(f'CALC:MARK:FUNC:CPOW:MODE {chann_mode}')
        self.sendSpecAnaCmd(f'CALC:MARK:FUNC:CPOW:UNIT {pow_unit}')
        time.sleep(RESPONSE_TIMEOUT)
        chann_bw = self.requestSpecAnaData(f'CALC:MARK:FUNC:CPOW:BAND?')
        chann_mode = self.requestSpecAnaData(f'CALC:MARK:FUNC:CPOW:MODE?')
        pow_unit = self.requestSpecAnaData(f'CALC:MARK:FUNC:CPOW:UNIT?')
        time.sleep(RESPONSE_TIMEOUT)
        print(f'Channel bandwidth = {(float(chann_bw.decode()) * 1e-6)} MHz')
        print(f'Channel mode = {chann_mode.decode()}')
        print(f'Power unit = {pow_unit.decode()}')

        return chann_bw, chann_mode, pow_unit

    def getSpecAnaPower(self):
        ''' Measure channel power

        This function sets the single sweep and reads the channel power from the device
        @params: None
        @return float: Measured channel power [dBm]
        '''
        self.configSpecAnaPow(args.chann_bw, args.chann_mode, args.pow_unit)
        # makes sure that the that the signal power level does not overload the R&S FSH
        self.sendSpecAnaCmd('CALC:MARK:FUNC:LEV:ONCE')  
        self.sendSpecAnaCmd('CALC:MARK:FUNC:POW ON')
        self.sendSpecAnaCmd('CALC:MARK:FUNC:POW:PRES "3GPP WCDMA.chpstd"')
        self.sendSpecAnaCmd('INIT:CONT OFF') 
        self.sendSpecAnaCmd('INIT;*WAI')
        self.sendSpecAnaCmd('SWE:TIME:AUTO ON')         # Auto sweep time
        self.sendSpecAnaCmd('CALC:MARK:FUNC:POW:SEL CPOW')
        chan_pow = self.requestSpecAnaData('CALC:MARK:FUNC:POW:RES? CPOW')
        power_spectral_density = float(chan_pow.decode()) - (10 * math.log(float(args.chann_bw), 10))
        self.sendSpecAnaCmd('CALC:MARK ON')
        self.sendSpecAnaCmd('CALC:MARK:FUNC:NOIS ON')
        #return print(f'Channel power is {chan_pow.decode()}')
        return print(f'Channel Power = {round(power_spectral_density, 2)} dBm/Hz')
        

if __name__ == '__main__':
    # Set up arguments to be parsed 
    parser = argparse.ArgumentParser(description = 'Specify spectrum analyzer channel power measurement parameters')
    parser.add_argument('freq_start', type = str, help = 'the start frequency incl. units (Hz)')
    parser.add_argument('freq_stop', type = str, help = 'the stop frequency incl. units (Hz)')
    parser.add_argument('chann_bw', type = str, help = 'the bandwidth of the channel in Hz')
    parser.add_argument('chann_mode', type = str, help = 'the channel mode: CLR Clear/Write, MAX Max Hold')
    parser.add_argument('pow_unit', type = str, help = 'the unit of the channel power')
    args = parser.parse_args()
    print("/------Setup spectrum analyser---------/")
    specAnal = SA_SOCK()
    specAnal.connectSpecAna((SA_ADDRESS))
    specAnal.setSpecAnaSweep(args.freq_start, args.freq_stop, NUMPOINTS)
    specAnal.setSpecAnaBandwidth('off', RBW, 'off', VBW)
    specAnal.setSpecAnaAmplitude(-10, 10) 
    specAnal.getSpecAnaPower()