
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 15:36:34 2019
@author: S. Malan
@modified by Vhulie 3 March 2022

1. connect to SG
2. Set up SG
3. connect to SA
4. Set up SA
5. Take a screenshoot

"""
#%%
#-----------------------Import functions that do the work--------------------#

#-----------------------import libaries for signal generator------------------#
import sys
import time
import socket
from RsInstrument import *
from numpy import double
from re import S
import pyvisa_py
import pyvisa
import matplotlib.pyplot as plt
import numpy as np
# will help when we want to plot the graph

sys.path.append('../sig_gen/') # adding signal generator path so that we can call a script from sig_gen folder
from sg_smb100a_output_discrete_freq_1 import sig_sock #Import the Signal Generator Socket class from sig_gen folder

#%%
#-----------------------import libraries for Spectrum analyzer----------------#
sys.path.append('../spec_ana/') # adding spectraum analyser path so that we can call a script from spec_ana folder
from sa_fsh8_setup_1.py import sa_sock #Import the Spectrum Analyser Socket Function

#%%
#-----------------------import libraries for Spectrum analyzer hcopy----------------#
from sa_fsh8_screen_grab_1 import sa_hcopy

#%%
#Constants and variable definitions
#.............................................................................#
#------------------------SA AND SG INITIALIZATION-----------------------------#
#.............................................................................#

#------------------------SA_FSH8 initializatio varaibles----------------------#
F_START = 100e6 #Start frequency
F_STOP = 2e9 #Stop frequency
NUMPONTS = 625 #Number of measurement points (Max=625)
RBW = 2e6 #Resolution BW of spectrum analyser
VBW = 300e3 #Video BW of spectrum analyser
REFLEV = 0 # Set reference level of spectrum analyser
ATTEN =0 #Set spectrum analyser attenuation
K = 1.38e-23 #Boltzman's constand
NUMMEAS = 5 #Set the number of measurements
#%%
# ------------------------SG_SMB100A constants Initialization varaiables-------#
POWER = 0.0                # Start RefLev [dBm]                              
FREQ = 100e3               # Start frequency Minimum 100kHz     
DEFAULT_TIMEOUT  = 1       # Default socket timeout
RF_STATE = 0               # Default RF Out state
#%%
#----------------------------SA_FSH8 socket connect--------------------------------#
specHOST = '10.8.88.232'
specPORT = 5555

#------------------------------SA_FSH8 Setup----------------------------------#
def setupSA():
    print("/------Setup spectrum analyser---------/")
    specAnal = sa_sock()
    specAnal.sa_connect((specHOST,specPORT))
    time.sleep(1) 
    specAnal.sa_sweep(f_start,f_stop,numPoints)
    time.sleep(1) 
    specAnal.sa_bw('off',Rbw,'off',Vbw) # Set the SA Resolution bandwidth mode to Manual, 100 KHz. Set the Video BW to Manual, 100 KHz 
    time.sleep(1) 
    specAnal.sa_amplitude(-10,10) 
    time.sleep(1) 
    #specAnal.sa_marker()
    time.sleep(1) 

    return specAnal
    # I guess running this as a function it should return something

#------------------------------SG_SMB100A socket connect ---------------------------#
sigHOST = '10.8.88.166'
sigPORT = 5025 # 18
#-----------------------------SG_SMB100A Setup---------------------------------------#
def setupSG():  
    print("/------Setup signal generator---------/")
    sigGen = sig_sock()                                 # Call main class
    sigGen.sig_gen_connect((sigHOST,sigPORT))           # Connect Sig Gen remotely
    time.sleep(1)                                       # Delay 1 sec
    sigGen.setRFOut('ON')                               # Activate Output signal                                
    #time.sleep(1)                                       # Delay 1 sec
    #sigGen.sigGenFreqs()                                # Activate frequency generator
    #time.sleep(1)                                       # Delay 1 sec
    sigGen.setSigGenPower(-20)                          # Sets Sig Gen power
    #time.sleep(1)                                       # Delay 1 sec
    #sigGen.closeGenSock()                               # Close socket
    print("/------End of Setup signal generator---------/")

    # i guess running this as as function it should return something
    return sigGen
    #-----------------------------SetUp Spectrum_Analyzer for Screenshot---------------------------------------#
    
    def sa_hcopy():
        SA_FSH8 = None
    try:
        # connecting via socket without using visa adjust the VISA Resources
        #Setting reset to True (default is False) resets your instrument. It is equivalent to calling the reset() method.
        #Setting id_query to True (default is True) checks, whether your instrument can be used with the RsInstrument module.
        #  "SelectVisa='socket'">>>Using RsInstrument without VISA for LAN Raw socket communication
        SA_FSH8 = RsInstrument('TCPIP::10.8.88.232::5555::SOCKET', False, False, "SelectVisa='socket'")
        SA_FSH8.opc_timeout = 3000  # Timeout for opc-synchronised operations
        SA_FSH8.instrument_status_checking = True  # Error check after each command
    except Exception as ex:
        print('Error initializing the instrument session:\n' + ex.args[0])
        exit()
    
    print(f'Device IDN: {SA_FSH8.idn_string}')
    print(f'Device Options: {",".join(SA_FSH8.instrument_options)}\n')

    #rth.clear_status()
    #rth.reset()
    ##set print to file
  
    file_path_SA_FSH8 = r'\Public\Screen Shots\test_capture1.png' # Instrument screenshoot file path
    #PC screenshoot file path(saved in googledrive)
    file_path_PC = r'/Users/vhulahani.manukha/Documents/git/test_capture1.png'
   
    ##  select file format
    SA_FSH8.write_str("HCOP:DEV:LANG PNG") 

    ## file path on instrument
    SA_FSH8.write_str(f"MMEM:NAME '{file_path_SA_FSH8}'")

    #create screenshot
    SA_FSH8.write_str_with_opc("HCOP:IMM") 

    #copy screenshoot from intrument to the pc
    SA_FSH8.read_file_from_instrument_to_pc(file_path_SA_FSH8, file_path_PC)
    
    SA_FSH8.close()

#%%   
# Main program
#-----------------------------------------------------------------------------   
if __name__ == '__main__':
    print("/------running main ---------/") 
    setupSG()
    time.sleep(1) 
    setupSA()
    time.sleep(1) 
    sa_hcopy()
    print("/------end  main ---------/") 

