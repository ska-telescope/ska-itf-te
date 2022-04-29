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
from sg_smb100a_generate_frequency_sweep_a import SG_SOCK #Import the Signal Generator Socket class from sig_gen folder

#%%
#-----------------------import libraries for Spectrum analyzer----------------#
sys.path.append('../spec_ana/') # adding spectraum analyser path so that we can call a script from spec_ana folder
from sa_fsh8_setup_rf_1_d import SA_SOCK #Import the Spectrum Analyser Socket Function
from sa_fsh8_setup_rf_1_d import power_values
from sa_fsh8_setup_rf_1_d import freq_values

# -----------------Connection Settings----------------------
SG_PORT = 5025                      # default SMB R&S port 
SG_HOST = '10.8.88.166'             # smb100a signal generator IP
SG_ADDRESS = (SG_PORT, SG_HOST)
SA_HOST = '10.8.88.138'            # fsh8 spectrum analyzer IP temporary
SA_PORT = 5555                     # fsh8 spectrum analyzer port 18? 23?
SA_ADDRESS = (SA_HOST, SA_PORT)
#-----------------------------------------------------------
# ----------------Initialization of Variables---------------    
DEFAULT_TIMEOUT = 1        # Default socket timeout
RF_OFF = 0
RF_ON = 1

freq_start = ''
freq_stop = ''
numPoints = 631
# ----------------------------------------------------------
# ----------------------------------------------------------
# -----------------SA AND SG INITIALIZATION-----------------
# ----------------------------------------------------------

#-----------------SA_FSH8 initialization Variables----------
f_start=100e6   # Start frequency
f_stop=2e9      # Stop frequency
numPoints=631   # Number of measurement points (Max=625)
Rbw=300e3         # Resolution BW of spectrum analyser
Vbw=300e3       # Video BW of spectrum analyser
RefLev=0        # Set reference level of spectrum analyser
Atten=0         # Set spectrum analyser attenuation
k=1.38e-23      # Boltzman's constand
numMeas=5       # Set the number of measurements
#%%
# ------------------------SG_SMB100A Initialization varaiables-------#
Power = 0.0                     # Start RefLev [dBm]                              
Freq = 900e3                    # Start frequency Minimum 900kHz     
default_timeout = 1             # Default socket timeout
rf_state = 0                    # Default RF Out state

#-------------------SG_SMB100A Setup-------------------------#
def setupSG():  
    print("/------Setup signal generator---------/")
    sigGen = SG_SOCK()                                 # Call main class
    sigGen.initSigGen((SG_HOST,SG_PORT))    
    time.sleep(1)
    sigGen.setSigGenRF(RF_ON)
    time.sleep(1)
    sigGen.setSigGenPower(-30)                                  
    print("/------End of Setup signal generator---------/")
    return sigGen

#------------------------SA_FSH8 Setup-------------------------#
def setupSA():
    print("/------Setup spectrum analyser---------/")
    specAnal = SA_SOCK()
    specAnal.sa_connect((SA_ADDRESS))
    time.sleep(1) 
    specAnal.sa_sweep(args.freq_start,args.freq_stop,numPoints)
    time.sleep(1) 
    specAnal.sa_bw('off',Rbw,'off',Vbw) # Set the SA Resolution bandwidth mode to Manual, 100 KHz. Set the Video BW to Manual, 100 KHz 
    time.sleep(1) 
    specAnal.sa_amplitude(-10,10) 
    time.sleep(1) 
    specAnal.sa_traceMaxHold()
    time.sleep(1)
    print("/------End of Setup Spectrum Analyzer---------/")
    return specAnal
        
#------------------------------ PLOT ---------------------------#
 # Write csv file
def plotTrace(freq_values, power_values): 
    # Filtering of power values above threshold
    filter_power_values = []
    for s in power_values:
        power_values_float = round(float(s),ndigits=2) 
        filter_power_values.append(int(power_values_float))
    print(f"power_values_list = {filter_power_values}.") 
    
    for power_value in filter_power_values:
        if power_value <= -45:
            filter_power_values.pop(power_value)
            freq_values.pop(power_value)
        print(f"Filtered power_values = {filter_power_values}.")
    # Write csv file    
    file = open (r'./Power_vs_Freq_LPF_Plot.csv', 'w')          # Open File for writing
    file.write("Frequency in kHz;Power in dBm\n")   # Write the headline
    x=0                                             # Set counter to 0 as touple does not begin with 1
    numPoints = len(freq_values)
    while x < numPoints:                       # Perform loop until all sweep points are covered
        file.write(str(freq_values[x]))             # Write amplitude measurement data
        file.write(";")                             # Add semicolon as CSV separator
        file.write(str(filter_power_values[x]))            # Write frequency data
        file.write("\n")                            # Add a new line control character
        x=x+1                                       # Increment counter
    file.close()

    # Plot the trace
    x_axis = freq_values
    y_axis = filter_power_values
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
    parser = argparse.ArgumentParser(description = "Specify Start and Stop Frequency")
    parser.add_argument("freq_start", type=str, help="the start frequency incl. units (Hz)")
    parser.add_argument("freq_stop", type=str, help="the stop frequency incl. units (Hz)")
    parser.add_argument("freq_step", type=str, help="the step frequency incl. units (Hz)")
    parser.add_argument("dwel_time", type=int, help="the sweep dwell time (ms)")
    args = parser.parse_args()

    print("/--------- Running main Code ---------/") 
    sg = setupSG()
    time.sleep(1) 
    sa = setupSA()
    time.sleep(1) 
    # Set Sig Gen to start freq, stop freq, step freq and dwell time
    sg.setSigGenSweep(args.freq_start, args.freq_stop, args.freq_step, args.dwel_time)    
    # set SA sweep parameters
    #sa.sa_getTraceParams(args.freq_start, args.freq_stop, args.freq_step)
    sa.sa_getTraceParams(args.freq_start, args.freq_stop)
    plotTrace(freq_values, power_values)
    print("Displayed plot...")
    print("End of program.")

