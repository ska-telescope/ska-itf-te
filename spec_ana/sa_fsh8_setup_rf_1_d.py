# -*- coding: utf-8 -*-
"""
Spectrum analyzer control via TCP/IP socket
Created on Wed Feb 09 11:41:11 2011
For an example, run this module and execute 'sa_example()'

@author: paulh
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

@modifier: Monde 
@Date: 11-04-2022
@Functional Description: 
    1. Added the frequency and power sweep array computation function
    2. Tidy docstrings
    3. File renaming to sa_fsh8_setup_rf_1_4.py
@Revision: 1_4
"""

#-------------------------- IMPORT REQUIRED PACKAGES-------------------------------------
import socket
import time
from numpy import double

# --------------------------CONNECTION SETTING-------------------------------------------
SA_HOST = '10.8.88.138'         # fsh8 spectrum analyzer IP
SA_PORT = 5555                  # fsh8 spectrum analyzer port 18? 23?
SA_ADDRESS = (SA_HOST, SA_PORT)

#--------------------------MEASUREMENTS CONSTANTS----------------------------------------

FREQ_STEP = 3015873             # step frequency in Hz

#-----------------------------------------------------------
# ----------------Initialization of Variables---------------    
DEFAULT_TIMEOUT = 1             # Default socket timeout
recdur = 5                      # Time in seconds to find maxhold peaks
power_values = []
freq_values = []
ampl_vals = []
freq_vals = []
# ----------------------------------------------------------

#-------------------------SPECTRUM ANALYZER SOCKET CLASS----------------------------------
class SA_SOCK(socket.socket):
    def sa_connect(self,address,default_timeout = 1,default_buffer = 1024,short_delay = 0.1,long_delay = 1):
        """ Establish socket connection.

        This function:
            Establishes a socket connection to the Spectrum Analyzer. Uses address (Including Port Number) as an argument.
            Performs a reset on the unit and sets the fixed frequency generator mode. 
            Sets the Display to On in Remote mode
            @params 
                SA_ADDRESS        :   SA_HOST str IP address of the device
                SA_PORT int port number to device access
                default_timeout     : int [Optional] Timeout for waiting to establish connection
                long_delay          : int
                short_delay         : int
                default_buffer      : int
        """
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
        print('SA detector mode set to = %s'%(det_mode_set))
        
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
        
    def sa_marker(self):
        """
        @return FLOAT: frequency [Hz]
        @return FLOAT: amplitude [dBm]
        """

        #Marker2 

        self.sa_sendcmd("CALC:MARK2 ON") 
        self.sa_sendcmd("CALC:MARK2:COUN ON") 
        self.sa_sendcmd("CALC:MARK2:CPE ON")
        self.sa_sendcmd("CALC:MARK2:MAX")
        freq_hz = self.sa_requestdata("CALC:MARK2:X?") # outputs the measured value
        amp_dbm = self.sa_requestdata("CALC:MARK2:Y?")
        return freq_hz, amp_dbm   

    def sa_traceMaxHold(self): 
    #     """
    #     function for trace max hold 
    #     """
        self.sa_sendcmd("DISP:TRAC:MODE MAXH")
        
        return print("Max and Hold Mode activated.")  

    def sa_getTraceParams(self, freq_start, freq_stop): 
        
        # Start frequency acquisition - return from args.str to int
        self.sa_sendcmd(f'SOUR:FREQ:STAR {freq_start}')
        time.sleep(1)
        self.sa_sendcmd('FREQ:STAR?')
        data = float(self.recv(1024))
        freq_start = data
        # End of start frequency acquisition

        # Stop frequency acquisition - return from args.str to int
        self.sa_sendcmd(f'SOUR:FREQ:STOP {freq_stop}')
        time.sleep(1)
        self.sa_sendcmd('FREQ:STOP?')
        data = float(self.recv(1024))
        freq_stop = data
        # End of stop frequency acquisition

        var_freq_step = 10000000            # From args.freq_step, for discussion
        No_Sweep_Points = int((freq_stop-freq_start)/var_freq_step) + 1

        #i = 0
        freq_hz = 0
        #while i < NoSweepPoints:
        #for i in range(0,(NoSweepPoints-1),1):
        for i in range(0,No_Sweep_Points,1):
            self.sa_sendcmd("CALC:MARK2 OFF")
            time.sleep(0.3)
            self.sa_sendcmd("CALC:MARK2 ON") 
            self.sa_sendcmd("CALC:MARK2:COUN ON") 
            self.sa_sendcmd("CALC:MARK2:CPE ON")
            time.sleep(0.3)
            #freq_values.append(freq_start + (i * FREQ_STEP))
            freq_values.append(freq_start + (i * var_freq_step))
            time.sleep(0.3)
            self.sa_sendcmd(f"CALC:MARK2:X {freq_values[i]}Hz")
            time.sleep(0.3)
            freq_hz = self.sa_requestdata("CALC:MARK2:X?")
            print(f"freq_hz = {freq_hz.decode()}") 
            time.sleep(0.3)
            amp_dbm = self.sa_requestdata("CALC:MARK2:Y?")
            print(f"amp_dbm = {amp_dbm.decode()}")                            
            power_values.append(amp_dbm.decode())
            #i = i + 1
            #time.sleep(1)
        #time.sleep(1)
        print("Power and Frequency Values acquired.")
        print(power_values, "\n", freq_values)
        return freq_values, power_values       

