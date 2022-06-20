#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: Vhuli / Monde 
@Date: 20-06-2022
@Affiliation: Test Engineers
@Functional Description: 
    1. This script generates discreet power values from -10 dBm to +10 dBm at 5 dB steps
    2. The parameters can be adjusted as per user requirements
    3. Run the script by parsing the following arguments on the terminal:
        - start power = -10, signed integer with no units [-10 dBm]
        - stop power = 5, unsigned integer with no units [5 dB]
        - step power = +10, signedinteger with no units [+10 dBm]
@Notes: 
    1. This script was written for the FSH8 Spectrum Analyzer and SMB100A Signal Generator. 
    2. Raw ethernet socket communication is used
        and thus VISA library/installation is not required
    3. This script uses scpi protocol for the automatic test equipment intended

@Revision: 1
'''

import sys
import time
import argparse
import matplotlib.pyplot as plt

sys.path.append('../sig_gen/') # adding signal generator path so that we can call a script from sig_gen folder
from sg_smb100a_generate_power_levels_1 import SG_SOCK # Import the Signal Generator Socket class from sig_gen folder
from sg_smb100a_generate_power_levels_1 import power
#%%
#-----------------------import libraries for Spectrum analyzer----------------#
sys.path.append('../spec_ana/')                 # adding spectraum analyser path so that we can call a script from spec_ana folder
from sa_fsh8_read_channel_power_at_different_levels_1 import SA_SOCK        # Import the Spectrum Analyser Socket Function
from sa_fsh8_read_channel_power_at_different_levels_1 import channel_power

# -----------------Connection Settings----------------------
SG_PORT = 5025                      # default SMB R&S port 
SG_HOST = '10.8.88.166'             # smb100a signal generator IP
SG_ADDRESS = (SG_HOST, SG_PORT)
SA_HOST = '10.8.88.138'             # fsh8 spectrum analyzer IP temporary
SA_PORT = 5555                      # fsh8 spectrum analyzer port 18? 23?
SA_ADDRESS = (SA_HOST, SA_PORT)
#-----------------------------------------------------------
# ----------------Initialization of Variables---------------    
DEFAULT_TIMEOUT = 1        # Default socket timeout
RF_OFF = 0
RF_ON = 1

# -----------------SA AND SG INITIALIZATION-----------------

#-----------------SA_FSH8 initialization Variables----------
NUMPOINTS = 631   # Number of measurement points (Max=625)
RBW = 3e6         # Resolution BW of spectrum analyser
VBW = 3e6       # Video BW of spectrum analyser
#%%
#-------------------SG_SMB100A Setup-------------------------#
def setupSG():  
    print('/------ Connect Signal Generator ---------/')
    sigGen = SG_SOCK()                                 # Call main class
    sigGen.connectSigGen(SG_ADDRESS) 
    print('/------End of Connect signal generator---------/')
    return sigGen

#------------------------SA_FSH8 Setup-------------------------#
def setupSA():
    print('/------Setup spectrum analyser---------/')
    specAnal = SA_SOCK()
    specAnal.connectSpecAna((SA_ADDRESS))
    specAnal.setSpecAnaBandwidth('off', RBW, 'off', VBW) # Set the SA Resolution bandwidth mode to Manual, 100 KHz. Set the Video BW to Manual, 100 KHz 
    specAnal.setSpecAnaAmplitude(-10, 10) 
    print('/------End of Setup Spectrum Analyzer---------/')
    return specAnal
        
#------------------------------ PLOT ---------------------------#
def plotTrace(channel_power_values, set_power_values): 
    ''' Plot response

    This function plots the power vs frequency filter response 

    @params:    
        freq_values: integer list [in Hz]
        power_value: integer list [in dBm]
    '''
    x_axis = channel_power_values 
    y_axis = set_power_values

    plt.plot(x_axis, y_axis)
    plt.xlabel('Channel Power in dBm')
    plt.ylabel('Power Set in dBm')
    plt.title('Channel Power Measurement')
    plt.show()

#%%   
# Main program
#-----------------------------------------------------------------------------   
if __name__ == '__main__':
    # Set up arguments to be parsed 
    parser = argparse.ArgumentParser(description = 'Specify Start and Stop Frequency')
    parser.add_argument('start_power', type = int, help = 'the start power incl. units (dBm)')
    parser.add_argument('stop_power', type = int, help = 'the stop power incl. units (dBm)')
    parser.add_argument('step_power', type = int, help = 'the step power incl. units (dBm)')
    parser.add_argument('freq_start', type = str, help = 'the start frequency incl. units (Hz)')
    parser.add_argument('freq_stop', type = str, help = 'the stop frequency incl. units (Hz)')
    parser.add_argument('chann_bw', type = str, help = 'the bandwidth of the channel in Hz')
    args = parser.parse_args()

    print('/--------- Running main Code ---------/') 
    SigGen = setupSG()
    time.sleep(1) 
    SpecAna = setupSA()
    time.sleep(1) 
    # Spectrum Analyzer Setup
    SpecAna.setSpecAnaSweep(args.freq_start, args.freq_stop, NUMPOINTS)
    
    # Setup Signal Generator
    cent_freq = SpecAna.requestSpecAnaData('FREQ:CENT?')
    SigGen.setSigGenFreq(cent_freq.decode())
    SigGen.setSigGenRF(RF_ON)

    # Set and read channel power values
    set_power = []
    current_power = args.start_power
    SigGen.setSigGenPower(current_power)
    while current_power <= args.stop_power:
        SigGen.setSigGenPower(current_power) 
        SpecAna.getSpecAnaPower(args.chann_bw)
        current_power += args.step_power
        set_power.append(current_power)
        time.sleep(0.01)

    print(channel_power, set_power)
    # Plot the results
    plotTrace(channel_power, set_power)
    print('Displayed plot...')
    print('End of program.')
