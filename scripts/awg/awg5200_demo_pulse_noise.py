"""
VISA: SourceXpress/AWG Sequence Builder and Channel Skew Adjuster
Author: Morgan Allison
Date created: 5/17
Date edited: 5/17
Creates a sequence of two waveforms with an external trigger dependency
and configures the AWG to change its phase between waveform outputs
Windows 7 64-bit
Python 3.6.0 64-bit (Anaconda 4.3.0)
NumPy 1.11.2, PyVISA 1.8, PyVISA-py 0.2
Download Anaconda: http://continuum.io/downloads
Anaconda includes NumPy
"""

import pyvisa as visa
import numpy as np

local_port = 10016
device_ip = "za-itf-awg.ad.skatelescope.org"


# Change this to connect to your AWG as needed
"""#################SEARCH/CONNECT#################"""
rm = visa.ResourceManager()
awg = rm.open_resource("TCPIP0::localhost::%i::SOCKET" % local_port)
awg.timeout = 25000
awg.encoding = 'latin_1'
awg.write_termination = '\n'
awg.read_termination = '\n'

print(awg.query('*idn?'))
awg.write('*rst')
awg.write('*cls')

record_length = 50000
sample_rate = 5e9 

##wave_name_1 = "new_wave_1"
##new_wave_data_1 = np.empty(record_length)

wave_name_2 = "new_wave_2"
new_wave_data_2 = np.empty(record_length)

##frequency_1 = 200e6
##frequency_2 = 240e6

noise_length = 5000

for i in range(0, record_length):
    if i < noise_length:
        new_wave_data_2[i] = (2 * np.random.random() - 1)
    else:
        new_wave_data_2[i] = 0

##new_wave_data = np.random.rand(record_length)
##new_wave_data = new_wave_data * 2 - 1

## Wipe all existing waveforms from memory.
awg.write('wlist:waveform:del all')

##awg.write('wlist:waveform:new "%s", %i' % (wave_name_1, record_length))
awg.write('wlist:waveform:new "%s", %i' % (wave_name_2, record_length))

##load_command_1 = 'wlist:waveform:data "%s", 0, %i, ' % (wave_name_1, record_length)
##awg.write_binary_values(load_command_1, new_wave_data_1)
##awg.query('*opc?')

load_command_2 = 'wlist:waveform:data "%s", 0, %i, ' % (wave_name_2, record_length)
awg.write_binary_values(load_command_2, new_wave_data_2)
awg.query('*opc?')

awg.write('clock:srate {}'.format(sample_rate))

##awg.write('source1:casset:waveform "%s"' % wave_name_1)
##awg.write('output1:state on')
awg.write('source2:casset:waveform "%s"' % wave_name_2)
awg.write('output2:state on')

awg.write('awgcontrol:run:immediate')
awg.query('*opc?')

print(awg.query('system:error:all?'))
awg.close()
