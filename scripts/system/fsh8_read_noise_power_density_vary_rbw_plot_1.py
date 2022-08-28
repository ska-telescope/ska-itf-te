#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@author: Vhuli and Monde 
@Date: 10-08-2022
@Affiliation: Test Engineers
@Functional Description: 
    1. This script reads the noise power density of the NC1113B noise source in dBm/Hz at different RBWs
    and plots power vs. frequency
    2. Run the script by parsing the following arguments on the terminal:
        - start frequency = 0 or 100e6, integer with no units [0 Hz]
        - stop frequency = 2000000000 or 3e9, integer with no units [3 GHz]
        - resolution bandwidth = 3000000 or 3e6, integer with no units [3 MHz]
 
@Notes: 
    1. This script was written for the FSH8 Spectrum Analyzer. 
        Raw ethernet socket communication is used and thus VISA library/installation is not required
    2. This script uses scpi protocol for the automatic test equipment intended

@Revision: 1
'''
import sys
import os
import time
import argparse
import matplotlib.pyplot as plt

#%%
#-----------------------import libraries for Spectrum analyzer----------------#
sys.path.insert(0, os.path.abspath(os.path.join('..') + '/spec_ana/'))
from sa_fsh8_read_noise_power_density import SA_SOCK        # Import the Spectrum Analyser Socket Function
from sa_fsh8_read_noise_power_density import pow_values
from sa_fsh8_read_noise_power_density import freq_values

# -----------------Connection Settings----------------------
SA_HOST = '10.8.88.138'             # fsh8 spectrum analyzer IP temporary
SA_PORT = 5555                      # fsh8 spectrum analyzer port 18? 23?
SA_ADDRESS = (SA_HOST, SA_PORT)
#-----------------------------------------------------------
# ----------------Initialization of Variables---------------    
DEFAULT_TIMEOUT = 1        # Default socket timeout
RF_OFF = 0
RF_ON = 1

# -----------------SA INITIALIZATION-----------------

#-----------------SA_FSH8 initialization Variables----------
NUMPOINTS = 631   # Number of measurement points (Max=625)

#------------------------SA_FSH8 Setup-------------------------#
def setupSA():
    print('/------Setup spectrum analyser---------/')
    specAnal = SA_SOCK()
    specAnal.connectSpecAna((SA_ADDRESS))
    specAnal.setSpecAnaSweep(args.freq_start, args.freq_stop, NUMPOINTS)
    rbw = args.res_bw           # Resolution BW of spectrum analyser
    vbw = args.vid_bw           # Video BW of spectrum analyser
    specAnal.setSpecAnaBandwidth('off', rbw, 'off', vbw) # Set the SA Resolution bandwidth mode to Manual, 100 KHz. Set the Video BW to Manual, 100 KHz 
    specAnal.setSpecAnaAmplitude(-25, 5) 
    specAnal.setSpecAnaDetector('rms')
    specAnal.setSpecAnaSweepTime('7.6s')
    specAnal.setMarkerFunction(args.marker_freq)
    print('/------End of Setup Spectrum Analyzer---------/')
    return specAnal
        
#------------------------------ PLOT ---------------------------#
def plotTrace(freq_values, pow_values): 
    ''' Plot response

    This function plots the power vs frequency filter response 

    @params:    
        freq_values: integer list [in Hz]
        power_value: integer list [in dBm]
    '''
    x_axis = freq_values
    y_axis = pow_values

    plt.plot(x_axis, y_axis)
    plt.xlabel('Frequency in GHz')
    plt.ylabel('Power in dBm')
    plt.title('Noise Power Density Response [dBm/Hz]')
    plt.show()

#%%   
# Main program
#-----------------------------------------------------------------------------   
if __name__ == '__main__':
    # Set up arguments to be parsed 
    parser = argparse.ArgumentParser(description = 'Specify Start and Stop Frequency')
    parser.add_argument('freq_start', type = str, help = 'the start frequency of the spectrum analyzer (Hz) e.g. 100000000 or 100e6, integer with no units [100 MHz, minimum 9 kHz]')
    parser.add_argument('freq_stop', type = str, help = 'the stop frequency of the spectrum analyzer (Hz) e.g. 2000000000 or 2e9, integer with no units [2 GHz, maximum 8 GHz]')
    parser.add_argument('res_bw', type = str, help = 'the resolution bandwidth of the spectrum analyzer (Hz) e.g. 3000000 or 3e6, integer with no units [3 MHz, odd multiples for FSH8]')
    parser.add_argument('vid_bw', type = str, help = 'the video bandwidth of the spectrum analyzer (Hz) e.g. 30, integer with no units [30 Hz, odd multiples for FSH8]')
    parser.add_argument('marker_freq', type = str, help = 'the frequency of interest on the spectrum analyzer (Hz) e.g. 100000000 or 100e6, integer with no units [100 MHz, minimum 9 kHz, maximum 8 GHz]')
    args = parser.parse_args()

    print('/--------- Running main Code ---------/') 
    time.sleep(1) 
    sa = setupSA()
    time.sleep(1) 
    run_time_delay = float(sa.requestSpecAnaData('SWE:TIME?').decode()) * float(10)
    for count in range(0, int(run_time_delay), 10):
        time.sleep(10)          # wait for sweep to complete  
        print(f'count = {count}...')
    sa.getSpecAnaTraceParams(args.freq_start, args.freq_stop)
    sa.closeSpecAna()
    plotTrace(freq_values, pow_values)
    print('Displayed plot...')
    print('End of program.')

