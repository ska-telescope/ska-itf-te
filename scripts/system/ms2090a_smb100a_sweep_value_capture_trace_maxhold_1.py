#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: Ben / Vhuli / Monde 
@Date: xx-09-2022
@Affiliation: Test Engineer
@Functional Description: 
    1. This script plots a frequency vs frequency from start freq to 2 GHz at 10 MHz steps
    2. The above parameters can be adjusted as per user requirements
    3. Run the script by parsing the following arguments on the terminal:
        - start frequency = 100000000 or 100e6, integer with no units [100 MHz]
        - stop frequency = 2000000000 or 2e9, integer with no units [2 GHz]
        - step frequency = 100000000 or 100e6, integer with no units [100 MHz]
        - dwell time = 1000, integer with no units [ms]
@Notes: 
    1. This script was written for the SMB100A Signal Generator and MS2090A Spectrum Analyzer. 
        Raw ethernet socket communication is used
        and thus VISA library/installation is not required
    2. This script uses scpi protocol for the automatic test equipment intended

@Revision: 1
'''
import sys
import os
import time
import argparse
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join('..') + '/sig_gen/'))
from sg_smb100a_generate_frequency_sweep_2 import SG_SOCK # Import the Signal Generator Socket class from sig_gen folder

#%%
#-----------------------import libraries for Spectrum analyzer----------------#
sys.path.insert(0, os.path.abspath(os.path.join('..') + '/spec_ana/ms2090a/'))
from sa_ms2090a_set_maxhold_read_trace_1 import SA_SOCK        # Import the Spectrum Analyser Socket Function

#--------Import scpi database for Signal Generator and Spectrum analyzer ----------#
sys.path.insert(1, os.path.abspath(os.path.join('../../') + '/resources/'))
from scpi_database import SGCmds
from scpi_database import SACmds

# -----------------Connection Settings----------------------
SG_PORT = 5025                    # default SMB R&S port 
SG_HOST = '10.20.7.1'             # smb100a signal generator IP
SG_ADDRESS = (SG_HOST, SG_PORT)
SA_HOST = '10.20.7.4'             # Anritsu spectrum analyzer IP temporary
SA_PORT = 9001                    # Anritsu spectrum analyzer port 18? 23?
SA_ADDRESS = (SA_HOST, SA_PORT)
#-----------------------------------------------------------
# ----------------Initialization of Variables---------------    
DEFAULT_TIMEOUT = 1        # Default socket timeout
RF_OFF = 0
RF_ON = 1

# -----------------SA AND SG INITIALIZATION-----------------

#-----------------SA initialization Variables----------
NUMPOINTS = 631   # Number of measurement points (Max=625)
RBW = 3e6         # Resolution BW of spectrum analyser
VBW = 3e6       # Video BW of spectrum analyser
#%%
#-------------------SG_SMB100A Setup-------------------------#
def setupSG():  
    print('/------Setup signal generator Class---------/\n')
    SG = SG_SOCK()                                 # Call main class
    SG.connectSG(SG_ADDRESS)    
    SG.setSGCmd(SGCmds['rf-state'], RF_ON)
    SG.setSGCmd(SGCmds['power'], -25)     
    print('/------End of Setup signal generator---------/\n\n')
    return SG
#------------------------SA_FSH8 Setup-------------------------#
def setupSA():
    print('/------Setup spectrum analyser---------/')
    SA = SA_SOCK()
    SA.connectSA((SA_ADDRESS))
    SA.setSACmd(SACmds['reset-device'])
    SA.setSACmd(SACmds['start-freq'], args.start_freq)
    SA.setSACmd(SACmds['stop-freq'], args.stop_freq)
    SA.setSACmd(SACmds['sweep-points'], NUMPOINTS)
    SA.setSACmd(SACmds['rbw-auto'], 'off')
    SA.setSACmd(SACmds['vbw-auto'], 'off')
    SA.setSACmd(SACmds['att-level'], 10)
    SA.setSACmd(SACmds['ref-level'], -10)
    SA.setSACmd(SACmds['det-auto-state'], 'OFF')
    SA.setSACmd(SACmds['det-mode'], 'RMS') 
    SA.setSACmd(SACmds['trace1-mode'], 'MAX')
    SA.setSACmd(SACmds['max-hold-state'], 'ON')
    
    print('/------End of Setup Spectrum Analyzer---------/\n\n')
    return SA
        
#------------------------------ PLOT ---------------------------#
def plotTrace(freq_values, power_values): 
    ''' Plot response

    This function plots the power vs frequency filter response 

    @params:    
        freq_values: integer list [in Hz]
        power_value: integer list [in dBm]
    '''
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
    parser.add_argument('start_freq', type = str, help = 'the start frequency incl. units (Hz)')
    parser.add_argument('stop_freq', type = str, help = 'the stop frequency incl. units (Hz)')
    parser.add_argument('step_freq', type = str, help = 'the step frequency incl. units (Hz)')
    parser.add_argument('dwel_time', type = int, help = 'the sweep dwell time (ms)')
    args = parser.parse_args()

    print('\n/--------- Running main Code ---------/') 
    sg = setupSG()
    time.sleep(1) 
    sa = setupSA()
    time.sleep(1) 

    # Set Sig Gen to start freq, stop freq, step freq and dwell time
    print("/------Setup Signal Generator Sweep Parameters... ---------/")

    '''
        This block of code generates a sweep frequency of the signal generator
        at 100MHz step
        @params:
            start_freq      : start frequency in Hz (not less than 9 kHz)
            stop_freq       : stop frequency in Hz (not more than 6 GHz)
            step_freq       : step frequency in Hz (default = 100 MHz)
            dwel_time       : duration of frequency output in ms (default=1000 ms)
        ''' 
    # Display SG start frequency
    start_freq_recvd = int(sg.getSGCmd(SACmds["start-freq"]).decode())
    print(f'Signal Generator Start Frequency = {float(start_freq_recvd)/1e6} MHz') 

    # Display SG stop frequency
    stop_freq_recvd = int(sg.getSGCmd(SACmds["stop-freq"]).decode())
    print(f'Signal Generator Stop Frequency = {float(stop_freq_recvd)/1e9} GHz')

    centFreq = (int(float(args.start_freq)) + int(float(args.stop_freq))) / 2
    span = int(float(args.stop_freq)) - int(float(args.start_freq))    
    span_recvd = int(sg.getSGCmd(SGCmds['span-freq']).decode())
    print(f"Sweep Span = {span_recvd/1e9} GHz")

        # 1. Set the sweep range
    sg.setSGCmd(SGCmds['cent-freq'], centFreq)
    centFreq_recvd = int(sg.getSGCmd(SGCmds['cent-freq']).decode())
    print(f"Sweep Center Frequency = {centFreq_recvd/1e9} GHz")
    sg.setSGCmd(SGCmds['span-freq'], span)

        # 2. Select linear or logarithmic spacing
    sg.setSGCmd(SGCmds['sweep-freq-spac-conf'], 'LIN')

        # 3. Set the step width and dwell time
    sg.setSGCmd(SGCmds['sweep-freq-step'], f'{args.step_freq}')
    step_freq_recvd = int(sg.getSGCmd(SGCmds['step-freq']).decode())
    print(f"Step Frequency = {step_freq_recvd/1e6} MHz")
    sg.setSGCmd(SGCmds['sweep-freq-dwell'], f'{args.dwel_time}')

        # 4. Select the trigger mode
    sg.setSGCmd(SGCmds['sweep-freq-trig'], 'SING')

        # 5. Select sweep mode and activate the sweep
    sg.setSGCmd(SGCmds['sweep-freq-mode'], 'AUTO')
    sg.setSGCmd(SGCmds['freq-mode'], 'SWE')

        # 6. Trigger the sweep     
    sg.setSGCmd(SGCmds['sweep-freq-exec'])
    print('Executing sweep...')

# ----------------End of Signal Generator Setup Sweep Parameters -----------------------
    # Wait until the sweep is finished
    run_time_delay = int((float(args.stop_freq) - float(args.start_freq)) / float(args.step_freq) * float(args.dwel_time / 1000) + 15)
    for count in range(0, run_time_delay, 10):
        time.sleep(10)          # wait for sweep to complete  
        print(f'count = {count}...')
    
    ''' Read trace data
        
    This block of code reads the power trace data and calculates the 
    trace frequency points

    @params:
        freq_start      : start frequency in Hz
        freq_stop       : stop frequency in Hz
    '''         
    
    freq_values = []
    power_values = [] 

    # Read and print Spectrum Analyzer start frequency
    start_freq = int(sa.getSACmd(SACmds["start-freq"]).decode())
    print(f'Spectrum Analyzer Start Frequency = {float(start_freq)/1e6} MHz') 

    # Read and print SA stop frequency
    stop_freq = int(sa.getSACmd(SACmds["stop-freq"]).decode())
    print(f'Spectrum Analyzer Stop Frequency = {float(stop_freq)/1e9} GHz')

    # Confugure trace data format to be Ascii
    sa.setSACmd(SACmds['data-format'], 'ASC')
    print('Trace data formatted to Ascii')   

    # Set single sweep
    sa.setSACmd((SACmds['sing-sweep-state']), 'OFF')

    # Get trace data power values  
    power_data = sa.getSACmd((SACmds['trace-data']), '1')
    time.time(0.1)
    power_data.decode()
    power_data = str(power_data)
    power_data.split(',') 
    No_of_Sweep_Points = int(sa.getSACmd(SACmds['sweep-points']))
    print(f'No_of_Sweep_Points = {No_of_Sweep_Points}')
    for s in power_data:
        power_data_float = round(float(s), 2) 
        power_values.append(power_data_float)

    freq_step_size = int((float(args.stop_freq) - int(float(args.start_freq))) / (No_of_Sweep_Points - 1))
    for i in range(0, No_of_Sweep_Points, 1):
        freq_values.append(int(float(args.freq_start)) + (i * freq_step_size))

    print('Power and Frequency Values acquired.')

    plotTrace(freq_values, power_values)

    sg.setSGCmd(SGCmds['rf-state'], RF_OFF)
    sg.closeSGSock()
    sa.closeSASock()

    plotTrace(freq_values, power_values)
    
    print('Displayed plot...')
    print('End of program.')
