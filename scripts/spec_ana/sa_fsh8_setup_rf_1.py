# -*- coding: utf-8 -*-
"""
Spectrum analyzer control via TCP/IP socket
Created on Wed Feb 09 11:41:11 2011
For an example, run this module and execute 'sa_example()'
@modify: Monde and Vhuli: 
        Date: 01-03-2022
        Affil: SKAO Test Engineers
        Description: 
        This script remotely controls basic parameters of the FSH8 spectrum analyzer
        The analyzer is the DUT i.e. there is no device connected at the input
        Mods:
        Added the host and port numbers
        Added initialization of f_start, f_stop, numPoints
        RBW, VBW, RefLev, Atten, k and numMeas
        Added funtion calls
"""

#-------------------------- IMPORT REQUIRED PACKAGES-------------------------------------

import socket
import time
from numpy import double
from RsInstrument import *
# --------------------------CONNECTION SETTING-------------------------------------------
specHOST = '10.8.88.138'            # fsh8 spectrum analyzer IP
specPORT = 5555                     # fsh8 spectrum analyzer port 18? 23?
address = (specHOST, specPORT)

#--------------------------MEASUREMENTS CONSTANTS----------------------------------------
f_start = 900e6 #Start frequency
f_stop = 1670e6 #Stop frequency
#f_stop=3000e6 #Stop frequency
numPoints = 625 #Number of measurement points (Max=625)
Rbw = 3000e3 #Resolution BW of spectrum analyser
Vbw = 300e3 #Video BW of spectrum analyser
# Rbw=3e6 #Resolution BW of spectrum analyser
# Vbw=3e6#Video BW of spectrum analyser
RefLev = -10 # Set reference level of spectrum analyser
Atten = 10 #Set spectrum analyser attenuation
k = 1.38e-23 #Boltzman's constand
numMeas = 5 #Set the number of measurements

#-------------------------SPECTRUM ANALYZER SOCKET CLASS----------------------------------
class sa_sock(socket.socket):
    """ A function to connect to the Spectrum Analyser. Uses address (Including Port Number) as an argument.
    Performs a reset on the unit and sets to Spectrum Analyser mode. Also sets the Display to On in Remote mode
    """   
    def connectSpecAna(self,address,default_timeout = 1,default_buffer = 1024,short_delay = 0.1,long_delay = 1):
        self.connect(address)  # connect to spectrum analyzer via socket at IP '10.8.88.138' and Port 5555
        # Mandatory timer and buffer setup.
        self.settimeout(default_timeout) 
        self.delay_long_s = long_delay
        self.delay_short_s = short_delay
        self.default_buffer = default_buffer
        # requesting instrument identity and print 
        rx_str = self.requestSpecAnaData('*IDN?') 
        print('Connected to: %s'%rx_str)
        self.sendSpecAnaCmd('*CLS') 
        # instrument reset.
        self.sendSpecAnaCmd('*RST')
        self.sendSpecAnaCmd('INST:SEL SAN')
        self.sendSpecAnaCmd('SYST:DISP:UPD ON')
        time.sleep(short_delay)
         
    def dumpSpecAnaData(self):
        while True:
            try:
                dump_str = self.recv(self.default_buffer)
                print('Dumping buffer data: %s'%dump_str)
            except socket.timeout:
                break

    def sendSpecAnaCmd(self,command_str):
#        A function to add \n at the end of any commands sent to the SA
        self.sendall(bytes(command_str, encoding='utf8') + b'\n')
                
    def requestSpecAnaData(self,request_str,response_buffer = 'default',timeout_max = 10):
#        A function to request trace data from the spectrum analyser. This 
        if type(response_buffer) == str:
            response_buffer = self.default_buffer
        self.dumpSpecAnaData()                                         # Cleanup the receive buffer
        self.sendSpecAnaCmd(request_str)                           # Send the request
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

    def setSpecAnaSweep(self,start_f = 0,stop_f = 100e6, nr_points = 625):
        """A function to set up the Spectrum Analyser Sweep
        Note that number of points can only be set to FSU(P): 155, 313, 625, 1251, 1999, 2501, 5001, 10001, 20001, 30001        
        """     
        self.sendSpecAnaCmd('FREQ:STAR %sHz'%start_f)
#        stop_f = start_f + (nr_points-1)*delta_f
        self.sendSpecAnaCmd('FREQ:STOP %sHz'%stop_f)
        self.sendSpecAnaCmd('SWE:POIN %s'%nr_points)
        start_f_set = double(self.requestSpecAnaData('FREQ:STAR?'))
        stop_f_set = double(self.requestSpecAnaData('FREQ:STOP?'))
        nr_points_set = int(self.requestSpecAnaData('SWE:POIN?'))
        print('SA Start Freq: %s MHz, Stop Freq: %s MHz, Points: %s'% \
              (start_f_set*1e-6,stop_f_set*1e-6,nr_points_set))
        
        return start_f_set,stop_f_set,nr_points_set #Returns the values reported by the SA
        
    def setSpecAnaBandwidth(self,rbw_auto = 'on', rbw = 0 ,vbw_auto = 'on',vbw = 0  ):
        """ Function to set the spectrum analyser resolution and video BW
        rbw_auto   : Set RBW auto 'on' or 'off' : 'on'|'off'
        rbw        : Sets the RBW in Hz for rbw_auto == 'on'
        vbw_auto   : Set VBW auto 'on' or 'off' : 'on'|'off'
        vbw        : Sets the VBW in Hz for vbw_auto == 'on 
        """
        if rbw_auto.upper() in ('ON','OFF'):
            self.sendSpecAnaCmd('BAND:AUTO %s'%rbw_auto.upper())
            rbw_auto_set = int(self.requestSpecAnaData('BAND:AUTO?'))
            if rbw_auto.upper() == 'OFF':
                self.sendSpecAnaCmd('BAND %s'%rbw)
                rbw_set = double(self.requestSpecAnaData('BAND?'))
            else:
                rbw_set = 0.0
                
        if vbw_auto.upper() in ('ON','OFF'):
            self.sendSpecAnaCmd('BAND:VID:AUTO %s'%vbw_auto.upper())
            vbw_auto_set = int(self.requestSpecAnaData('BAND:VID:AUTO?'))
            if vbw_auto.upper() == 'OFF':
                self.sendSpecAnaCmd('BAND:VID %s'%vbw)
                vbw_set = double(self.requestSpecAnaData('BAND:VID?'))
            else:
                vbw_set = 0.0    
                
        print('SA RBW set to AUTO %i, RBW = %0.2f KHz'%(rbw_auto_set,rbw_set*1e-3))
        print('SA VBW set to AUTO %i, VBW = %0.2f KHz'%(vbw_auto_set,vbw_set*1e-3))
    
    
    def sa_detect(self,det_mode = 'rms'):
        """ Method that sets the detector mode of the Spectrum analyzer
        det_mode   : Sets the detector mode     : 'APE' (Autopeak)|'POS'|'NEG'|'SAMP'|'RMS'|'AVER'|'QPE' (Quasipeak)
        trace_mode : Sets the trace mode        : 'WRIT' (Clear/Write)|'MAXH'|'AVER'|'VIEW'
        """
        self.sendSpecAnaCmd('DET %s'%det_mode.upper())
        det_mode_set = self.requestSpecAnaData('DET?')
        trace_mode_set = self.requestSpecAnaData('DISP:WIND:TRAC:MODE?')
        print('SA detector mode set to = %s'%(det_mode_set))
        
    def setSpecAnaAmplitude(self, ref_level_dBm = 0, att_level_dB = 10):
        """ Method that sets the amplitude parameters for the spectrum analyzer and sets the attenuator
        ref_level_dBm    : Sets the reference level [dBm]
        """
     
        self.sendSpecAnaCmd('INP:ATT:AUTO OFF')
        time.sleep(5)
        self.sendSpecAnaCmd('INP:ATT %i dB' % att_level_dB)
        self.sendSpecAnaCmd('DISP:WIND:TRAC:Y:RLEV %i' % ref_level_dBm)
        ref_level_dBm_set = double(self.requestSpecAnaData('DISP:WIND:TRAC:Y:RLEV?'))
        att_level_dB_set = double(self.requestSpecAnaData('INP:ATT?'))
        print('SA amplitude reference level set to REF %0.2f dBm' % (ref_level_dBm_set))
        print('SA input attenuator set to %s dB'%(att_level_dB_set))
        
    def getSpecAnaSweepData(self,maximum_wait_time_s = 10*60):
        """ Method that starts a new sweep and downloads the data, returned as a list
        Returns a list of the measured data in [dBm]
        """
        self.dumpSpecAnaData()
        self.sendSpecAnaCmd('INIT1:CONT OFF')
        self.sendSpecAnaCmd('INIT1')
        rx_str = self.requestSpecAnaData('*OPC?','default',maximum_wait_time_s)
        return list(eval(self.requestSpecAnaData('TRACE1? TRACE1')))
        
    def sa_marker(self):
        """ @return FLOAT: frequency [Hz]
        @return FLOAT: amplitude [dBm]
        """
        self.sendSpecAnaCmd("CALC:MARK2 ON") 
        self.sendSpecAnaCmd("CALC:MARK2:COUN ON") 
        self.sendSpecAnaCmd("CALC:MARK2:CPE ON")
        self.sendSpecAnaCmd("CALC:MARK2:MAX")
        freq_hz = self.requestSpecAnaData("CALC:MARK2:X?") # outputs the measured value
        amp_dbm = self.requestSpecAnaData("CALC:MARK2:Y?")
        return [freq_hz, amp_dbm]   

    def sa_traceMaxHold(self): 
        """ function for trace max hold """
        self.sendSpecAnaCmd("DISP:TRAC:MODE MAXH")
        return         

    
# we need to 
    # def sa_tracePlot(self):
    #     fmin = 60
    #     step_size = 0.1
    #     FREQLIST = []
    #     for step_number in range(630):
    #         Frequency =  fmin + step_number * step_size 
    #         FREQLIST.append(Frequency)
    #     return    

if __name__ == '__main__':
    print("/------Setup spectrum analyser---------/")
    specAnal = sa_sock()
    specAnal.sa_connect((specHOST,specPORT))
    specAnal.setSpecAnaSweep(f_start,f_stop,numPoints)
    specAnal.sa_bw('off', Rbw, 'off', Vbw)
    specAnal.sa_amplitude(RefLev, Atten) 
    specAnal.sa_marker()
