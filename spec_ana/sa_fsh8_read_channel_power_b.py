#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vhuli and Monde 
@Date: 20-05-2022
@Affiliation: Test Engineers
@Functional Description: 
    1. This script reads the power of the channel in dBm
    2. The parameters can be adjusted as per user requirements
    3. Run the script by parsing the following arguments on the terminal:
        - chann_bw: the bandwidth ofthe channel in Hz e.g. 3000000 or 3e6, integer with no units [3 MHz]
        - chann_mode: the channel mode e.g. 'CLR' for Clear/Write, 'MAX' for Max Hold, string with ''
        - pow_unit, the unit of the channel power e.g. 'DBM' | 'DBMV' | 'DBUV' | 'VOLT' | 'WATT' | 'V' | 'W', string with ''

@Notes: 
    1. This script was written for the FSH8 Spectrum Analyzer. 
        Raw ethernet socket communication is used and thus VISA library/installation is not required
    2. This script uses scpi protocol for the automatic test equipment intended

@Revision: 0_1
"""

#-------------------------- IMPORT REQUIRED PACKAGES-------------------------------------
import socket
import time
from numpy import double
import argparse
# --------------------------CONNECTION SETTING-------------------------------------------
SA_HOST = '10.8.88.138'         # fsh8 spectrum analyzer IP
SA_PORT = 5555                  # fsh8 spectrum analyzer port 18? 23?
SA_ADDRESS = (SA_HOST, SA_PORT)

#--------------------------MEASUREMENTS CONSTANTS----------------------------------------

f_start=900e6 #Start frequency
f_stop=1670e6 #Stop frequency
#f_stop=3000e6 #Stop frequency
numPoints=625 #Number of measurement points (Max=625)
Rbw=300e3 #Resolution BW of spectrum analyser
Vbw=300e3 #Video BW of spectrum analyser
# Rbw=3e6 #Resolution BW of spectrum analyser
# Vbw=3e6#Video BW of spectrum analyser
RefLev=0 # Set reference level of spectrum analyser
Atten=0 #Set spectrum analyser attenuation
k=1.38e-23 #Boltzman's constand
numMeas=5 #Set the number of measurements
#-----------------------------------------------------------
# ----------------Initialization of Variables---------------    
DEFAULT_TIMEOUT = 1             # Default socket timeout

# ----------------------------------------------------------

#-------------------------SPECTRUM ANALYZER SOCKET CLASS----------------------------------
class SA_SOCK(socket.socket):
# A function to connect to the Spectrum Analyser. Uses address (Including Port Number) as an argument.
# Performs a reset on the unit and sets to Spectrum Analyser mode. Also sets the Display to On in Remote mode
    def sa_connect(self,address,default_timeout = 1,default_buffer = 1024,short_delay = 0.1,long_delay = 1):
        self.connect(address)  # connect to spectrum analyzer via socket at IP '10.8.88.138' and Port 5555
        # Mandatory timer and buffer setup.
        self.settimeout(default_timeout) 
        self.delay_long_s = long_delay
        self.delay_short_s = short_delay
        self.default_buffer = default_buffer

        rx_str = self.sa_requestdata('*IDN?') # requesting instrument identity and print 
        print('Connected to: %s'%rx_str)
        self.sa_sendcmd('*CLS')                                     
        self.sa_sendcmd('*RST')# instrument reset.
        self.sa_sendcmd('INST:SEL SAN')
        self.sa_sendcmd('SYST:DISP:UPD ON')
        time.sleep(short_delay)

    #         
    def sa_dumpdata(self):
        while True:
            try:
                dump_str = self.recv(self.default_buffer)
                print('Dumping buffer data: %s'%dump_str)
            except socket.timeout:
                break

    def sa_sendcmd(self,command_str):
#        A function to add \n at the end of any commands sent to the SA
        self.sendall(bytes(command_str, encoding='utf8') + b'\n')
                
    def sa_requestdata(self,request_str,response_buffer = 'default',timeout_max = 10):
#        A function to request trace data from the spectrum analyser. This 
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
                    time.sleep(self.delay_short_s)                  # No response, keep waiting
            else:
                if return_str.endswith(b'\n'):                      # Test to see if end of line has been reached, i.e. all the data Rx
                    return return_str[:-1]                         # Return string

    def sa_sweep(self,start_f = 0,stop_f = 100e6, nr_points = 625):
#        A function to set up the Spectrum Analyser Sweep
# Note that number of points can only be set to FSU(P): 155, 313, 625, 1251, 1999, 2501, 5001, 10001, 20001, 30001        
        
        self.sa_sendcmd('FREQ:STAR %sHz'%start_f)
#        stop_f = start_f + (nr_points-1)*delta_f
        self.sa_sendcmd('FREQ:STOP %sHz'%stop_f)
        self.sa_sendcmd('SWE:POIN %s'%nr_points)
        start_f_set = double(self.sa_requestdata('FREQ:STAR?'))
        stop_f_set = double(self.sa_requestdata('FREQ:STOP?'))
        nr_points_set = int(self.sa_requestdata('SWE:POIN?'))
        print('SA Start Freq: %s MHz, Stop Freq: %s MHz, Points: %s'% \
              (start_f_set*1e-6,stop_f_set*1e-6,nr_points_set))
        
        return start_f_set,stop_f_set,nr_points_set #Returns the values reported by the SA
        
    def sa_bw(self,rbw_auto = 'on', rbw = 0 ,vbw_auto = 'on',vbw = 0  ):
#   Function to set the spectrum analyser resolution and video BW
#        rbw_auto   : Set RBW auto 'on' or 'off' : 'on'|'off'
#        rbw        : Sets the RBW in Hz for rbw_auto == 'on'
#        vbw_auto   : Set VBW auto 'on' or 'off' : 'on'|'off'
#        vbw        : Sets the VBW in Hz for vbw_auto == 'on'
        if rbw_auto.upper() in ('ON','OFF'):
            self.sa_sendcmd('BAND:AUTO %s'%rbw_auto.upper())
            rbw_auto_set = int(self.sa_requestdata('BAND:AUTO?'))
            if rbw_auto.upper() == 'OFF':
                self.sa_sendcmd('BAND %s'%rbw)
                rbw_set = double(self.sa_requestdata('BAND?'))
            else:
                rbw_set = 0.0
                
        if vbw_auto.upper() in ('ON','OFF'):
            self.sa_sendcmd('BAND:VID:AUTO %s'%vbw_auto.upper())
            vbw_auto_set = int(self.sa_requestdata('BAND:VID:AUTO?'))
            if vbw_auto.upper() == 'OFF':
                self.sa_sendcmd('BAND:VID %s'%vbw)
                vbw_set = double(self.sa_requestdata('BAND:VID?'))
            else:
                vbw_set = 0.0    
                
        print('SA RBW set to AUTO %i, RBW = %0.2f kHz'%(rbw_auto_set,rbw_set*1e-3))
        print('SA VBW set to AUTO %i, VBW = %0.2f kHz'%(vbw_auto_set,vbw_set*1e-3))
    
    
    def sa_detect(self,det_mode = 'rms'):
#        ''' Method that sets the detector mode of the Spectrum analyzer
#        det_mode   : Sets the detector mode     : 'APE' (Autopeak)|'POS'|'NEG'|'SAMP'|'RMS'|'AVER'|'QPE' (Quasipeak)
#        trace_mode : Sets the trace mode        : 'WRIT' (Clear/Write)|'MAXH'|'AVER'|'VIEW'
#        '''
        self.sa_sendcmd('DET %s'%det_mode.upper())
        det_mode_set = self.sa_requestdata('DET?')
        trace_mode_set = self.sa_requestdata('DISP:WIND:TRAC:MODE?')
        print(f"SA detector mode set to = {det_mode_set.decode()}")
        
    def sa_amplitude(self,ref_level_dBm = 0, att_level_dB = 5):
        ''' Method that sets the amplitude parameters for the spectrum analyzer and sets the attenuator
        ref_level_dBm    : Sets the reference level [dBm]'''
     
        self.sa_sendcmd('INP:ATT:AUTO OFF')
        self.sa_sendcmd('DISP:WIND:TRAC:Y:RLEV %sdBm'%ref_level_dBm)

        self.sa_sendcmd('INP:ATT %s dB'%att_level_dB)
        ref_level_dBm_set = double(self.sa_requestdata('DISP:WIND:TRAC:Y:RLEV?'))
        att_level_dB_set = double(self.sa_requestdata('INP:ATT?'))
        print('SA amplitude reference level set to REF %0.2f dBm'%(ref_level_dBm_set))
        print('SA input attenuator set to %s dB'%(att_level_dB_set))
        
    def sa_getsweepdata(self,maximum_wait_time_s = 10*60):
        ''' Method that starts a new sweep and downloads the data, returned as a list
        Returns a list of the measured data in [dBm]
        '''
        self.sa_dumpdata()
        self.sa_sendcmd('INIT1:CONT OFF')
        self.sa_sendcmd('INIT1')
        rx_str = self.sa_requestdata('*OPC?','default',maximum_wait_time_s)
        return list(eval(self.sa_requestdata('TRACE1? TRACE1')))

#    This part of the script is pending testing when the Spectrum Analyzer is accessible

    def sa_CPOWConfig(self, chann_bw, chann_mode, pow_unit):
        """Set channel bandwidth, channel power mode and power unit

        This function sets the channel bandwidth for power measurement
        @params: None  
        """
        self.sa_detect('rms')
        self.sa_sendcmd(f"CALC:MARK:FUNC:CPOW:BAND {chann_bw} Hz")
        self.sa_sendcmd(f"CALC:MARK:FUNC:CPOW:MODE {chann_mode}")
        self.sa_sendcmd(f"CALC:MARK:FUNC:CPOW:UNIT {pow_unit}")
        chann_bw = self.sa_requestdata(f"CALC:MARK:FUNC:CPOW:BAND?")
        chann_mode = self.sa_requestdata(f"CALC:MARK:FUNC:CPOW:MODE?")
        pow_unit = self.sa_requestdata(f"CALC:MARK:FUNC:CPOW:UNIT?")
        print(f"Channel bandwidth = {chann_bw.decode()} Hz")
        print(f"Channel mode = {chann_mode.decode()}")
        print(f"Power unit = {pow_unit.decode()}")
        return

    def sa_getChannelPower(self):
        """Measure channel power

        This function reads the channel power from the device
        @params: None
        @return FLOAT: Measured channel power [dBm]
        """
        self.sa_CPOWConfig(args.chann_bw, args.chann_mode, args.pow_unit)
        self.sa_sendcmd("CALC:MARK:FUNC:POW:PRES '3GPP WCDMA.chpstd'")
        self.sa_sendcmd("INIT:CONT OFF") 
        self.sa_sendcmd("CALC:MARK:FUNC:POW ON")
        self.sa_sendcmd("CALC:MARK:FUNC:POW:SEL CPOW")
        self.sa_sendcmd("INIT;*WAI")
        chan_pow = self.sa_requestdata("CALC:MARK:FUNC:POW:RES? CPOW")
        print(f"Channel power is {chan_pow.decode()}")
        return

if __name__ == '__main__':
    # Set up arguments to be parsed 
    parser = argparse.ArgumentParser(description = "Specify channel bandwidth, channel mode and channel power units parameters")
    parser.add_argument("chann_bw", type=str, help="the bandwidth of the channel in Hz")
    parser.add_argument("chann_mode", type=str, help="the channel mode: CLR Clear/Write, MAX Max Hold")
    parser.add_argument("pow_unit", type=str, help="the unit of the channel power")
    args = parser.parse_args()
    print("/------Setup spectrum analyser---------/")
    specAnal = SA_SOCK()
    specAnal.sa_connect((SA_ADDRESS))
    specAnal.sa_sweep(f_start,f_stop,numPoints)
    specAnal.sa_bw('off',Rbw,'off',Vbw)
    specAnal.sa_amplitude(-10,10) 
    specAnal.sa_getChannelPower()