#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Monde 
@Date: 05-04-2022
@Affiliation: Test Engineer
@Functional Description: 
    1. This script plots a frequency vs frequency from start freq to 2 GHz at 10 MHz steps
    2. The above parameters can be adjusted as per user requirements
    3. Run the script by parsing the following arguments on the terminal:
        - start frequency = 100000000 or 100e6, integer with no units [100 MHz]
        - stop frequency = 2000000000 or 2e9, integer with no units [2 GHz]
@Notes: 
    1. This script was written for the SMB100A Signal Generator and FSH8 Spectrum Analyzer. 
        Raw ethernet socket communication is used
        and thus VISA library/installation is not required
    2. This script uses scpi protocol for the automatic test equipment intended

@Revision: 0_1
"""
import sys
import time
import argparse
import matplotlib.pyplot as plt

sys.path.append('../sig_gen/') # adding signal generator path so that we can call a script from sig_gen folder
from sg_smb100a_generate_frequency_sweep_1 import SG_SOCK # Import the Signal Generator Socket class from sig_gen folder

#%%
#-----------------------import libraries for Spectrum analyzer----------------#
sys.path.append('../spec_ana/')                 # adding spectraum analyser path so that we can call a script from spec_ana folder
from sa_fsh8_set_maxhold_read_trace_1 import SA_SOCK        # Import the Spectrum Analyser Socket Function
from sa_fsh8_set_maxhold_read_trace_1 import power_values
from sa_fsh8_set_maxhold_read_trace_1 import freq_values

# -----------------Connection Settings----------------------
SG_PORT = 5025                      # default SMB R&S port 
SG_HOST = '10.8.88.166'             # smb100a signal generator IP
SG_ADDRESS = (SG_PORT, SG_HOST)
SA_HOST = '10.8.88.138'             # fsh8 spectrum analyzer IP temporary
SA_PORT = 5555                      # fsh8 spectrum analyzer port 18? 23?
SA_ADDRESS = (SA_HOST, SA_PORT)
#-----------------------------------------------------------
# ----------------Initialization of Variables---------------    
DEFAULT_TIMEOUT = 1        # Default socket timeout
RF_OFF = 0
RF_ON = 1

freq_start = ''
freq_stop = ''
numPoints = 631
# -----------------SA AND SG INITIALIZATION-----------------

#-----------------SA_FSH8 initialization Variables----------
NUMPOINTS = 631   # Number of measurement points (Max=625)
RBW = 3e6         # Resolution BW of spectrum analyser
VBW = 300e3       # Video BW of spectrum analyser
#%%
#-------------------SG_SMB100A Setup-------------------------#
def setupSG():  
    print("/------Setup signal generator---------/")
    sigGen = SG_SOCK()                                 # Call main class
    sigGen.initSigGen((SG_HOST, SG_PORT))    
    sigGen.setSigGenRF(RF_ON)
    sigGen.setSigGenPower(-30)     
    print("/------End of Setup signal generator---------/")
    return sigGen

#------------------------SA_FSH8 Setup-------------------------#
def setupSA():
    print("/------Setup spectrum analyser---------/")
    specAnal = SA_SOCK()
    specAnal.sa_connect((SA_ADDRESS))
    specAnal.sa_sweep(args.freq_start, args.freq_stop, NUMPOINTS)
    specAnal.sa_bw('off', RBW, 'off', VBW) # Set the SA Resolution bandwidth mode to Manual, 100 KHz. Set the Video BW to Manual, 100 KHz 
    specAnal.sa_amplitude(-10, 10) 
    specAnal.sa_traceMaxHold()
    print("/------End of Setup Spectrum Analyzer---------/")
    return specAnal
        
#------------------------------ PLOT ---------------------------#
 # Write csv file
def plotTrace(freq_values, power_values): 
    # Plot the trace
    x_axis = freq_values
    y_axis = power_values

    plt.plot(x_axis, y_axis)
    plt.xlabel('Frequency in GHz')
    plt.ylabel('Power in dBm')
    plt.title('Low Pass Filter Response')
    plt.show()

#%%   
# Main program
#-----------------------------------------------------------------------------   
if __name__ == '__main__':
    # Set up arguments to be parsed 
    parser = argparse.ArgumentParser(description = 'Specify Start and Stop Frequency')
    parser.add_argument('freq_start', type = str, help = 'the start frequency incl. units (Hz)')
    parser.add_argument('freq_stop', type = str, help = 'the stop frequency incl. units (Hz)')
    parser.add_argument('freq_step', type = str, help = 'the step frequency incl. units (Hz)')
    parser.add_argument('dwel_time', type = int, help = 'the sweep dwell time (ms)')
    args = parser.parse_args()

    print("/--------- Running main Code ---------/") 
    sg = setupSG()
    time.sleep(1) 
    sa = setupSA()
    time.sleep(1) 
    # Set Sig Gen to start freq, stop freq, step freq and dwell time
    sg.setSigGenSweep(args.freq_start, args.freq_stop, args.freq_step, args.dwel_time) 
    run_time_delay = int((float(args.freq_stop) - float(args.freq_start)) / float(args.freq_step) * float(args.dwel_time / 1000) + 15)
    
    print(f'Run time delay = {run_time_delay}')
    for count in range(0, run_time_delay, 10):
        time.sleep(10)          # wait for sweep to complete  
        print(f'count = {count}...')
    
    sa.sa_getTraceParams(args.freq_start, args.freq_stop)
    plotTrace(freq_values, power_values)
    print("Displayed plot...")
    print("End of program.")

