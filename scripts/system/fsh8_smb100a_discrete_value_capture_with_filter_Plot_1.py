
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author:  Vhulie and Monde 3 March 2022
1. Connect to SG
2. Set up SG
3. Connect to SA
4. Set up SA
5. FOR Loop
6. append to lists x.append(number)
"""
#%%
#-----------------------Import functions that do the work--------------------#

#-----------------------import libaries for signal generator------------------#
import sys
import os
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

sys.path.insert(0, os.path.abspath(os.path.join('..') + '/sig_gen/'))
from sg_smb100a_output_discrete_freq_1 import sig_sock #Import the Signal Generator Socket class from sig_gen folder

#%%
#-----------------------import libraries for Spectrum analyzer----------------#
sys.path.insert(0, os.path.abspath(os.path.join('..') + '/spec_ana/'))
from sa_fsh8_setup_rf_1 import sa_sock #Import the Spectrum Analyser Socket Function

#%%
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
specHOST = '10.8.88.138' # changed port to from 138 to 232
specPORT = 5555

#------------------------------SA_FSH8 Setup----------------------------------#
def setupSA():
    print("/------Setup spectrum analyser---------/")
    specAnal = sa_sock()
    specAnal.sa_connect((specHOST,specPORT))
    time.sleep(1) 
    specAnal.sa_sweep(F_START,F_STOP,NUMPONTS)
    time.sleep(1) 
    specAnal.sa_bw('off',RBW,'off',VBW) # Set the SA Resolution bandwidth mode to Manual, 100 KHz. Set the Video BW to Manual, 100 KHz 
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
    sigGen.setSigGenPower(-30)                          # Sets Sig Gen power
    sigGen.setRFOut('ON')                               # Activate Output signal                                
    print("/------End of Setup signal generator---------/")
    # i guess running this as as function it should return something
    return sigGen
    #-----------------------------SetUp Spectrum_Analyzer for Screenshot---------------------------------------#
    
#%%   
# Main program
#-----------------------------------------------------------------------------   
if __name__ == '__main__':
    print("/------running main ---------/") 
    freq_vals = []
    ampl_vals = []
    sg = setupSG()
    time.sleep(1) 
    sa = setupSA()
    time.sleep(1) 

    for x in range(20):
        sg.setSigGenFreq((x+1) * 100e6)
        time.sleep(1)
        marker_val = sa.sa_marker()
        freq_vals.append(float(marker_val[0]))
        ampl_vals.append(float(marker_val[1]))

    
    sg.closeGenSock()

    print(freq_vals)
    print(ampl_vals)
    plt.plot(freq_vals, ampl_vals)
    plt.xlabel('Frequecy in Hz')
    plt.ylabel('Amplitude in dBm')
    plt.savefig("Power as function frequency.pdf")
    plt.grid()
    plt.show()

    print("/------end  main ---------/") 

