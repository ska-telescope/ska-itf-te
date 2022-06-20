
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
.
.
.
5. FOR Loop
6. append to lists x.append(number)
7. copy and paste those numbers for now into an email to me

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
from sg_smb100a_output_discrete_freq_a import sig_sock #Import the Signal Generator Socket class from sig_gen folder

#%%
#-----------------------import libraries for Spectrum analyzer----------------#
sys.path.append('../spec_ana/') # adding spectraum analyser path so that we can call a script from spec_ana folder
from sa_fsh8_setup_rf_1 import sa_sock #Import the Spectrum Analyser Socket Function

#%%
#%%
#Constants and variable definitions
#.............................................................................#
#------------------------SA AND SG INITIALIZATION-----------------------------#
#.............................................................................#

#------------------------SA_FSH8 initializatio varaibles----------------------#
f_start=100e6 #Start frequency
f_stop=2e9 #Stop frequency
numPoints=625 #Number of measurement points (Max=625)
Rbw=2e6 #Resolution BW of spectrum analyser
Vbw=300e3 #Video BW of spectrum analyser
RefLev=0 # Set reference level of spectrum analyser
Atten=0 #Set spectrum analyser attenuation
k=1.38e-23 #Boltzman's constand
numMeas=5 #Set the number of measurements
#%%
# ------------------------SG_SMB100A constants Initialization varaiables-------#
Power = 0.0                     # Start RefLev [dBm]                              
Freq = 100e3                    # Start frequency Minimum 100kHz     
default_timeout = 1             # Default socket timeout
rf_state = 0                    # Default RF Out state
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

    print(freq_vals)
    print(ampl_vals)
    plt.plot(freq_vals, ampl_vals)
    plt.xlabel('Frequecy in Hz')
    plt.ylabel('Amplitude in dBm')
    plt.savefig("Power as function frequency.pdf")
    plt.grid()
    plt.show()

    print("/------end  main ---------/") 

