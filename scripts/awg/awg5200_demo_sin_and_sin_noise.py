"""
Creates a sequence of two waveforms, one sinusoid and one sinusoid with noise
Author: Benjamin Lunsky 
Date created: 30/08/2022
"""

import pyvisa
import numpy as np

# Change this to connect to your AWG as needed
"""#################SEARCH/CONNECT#################"""
rm = pyvisa.ResourceManager('@py')
awg = rm.open_resource('TCPIP::10.165.3.3::INSTR')
awg.timeout = 50000
awg.encoding = 'latin_1'
awg.write_termination = '\n'
awg.read_termination = '\n'
print(awg.query('*idn?'))
awg.write('*rst')
awg.write('*cls')

recordLength = 50000
sampleRate = 2.5e9

name1 = "SineTest"
name2 = "NoisySineTest"

awg.write('wlist:waveform:del all')

import numpy as np
dur = 50000
f0 = 26e6
fs = 2.5e9
t = np.arange(dur)
sinusoid = np.sin(2 * np.pi * t * (f0 / fs))
noisysinusoid = np.sin(2 * np.pi * t * (f0 / fs)) + np.random.normal(0, 1, dur)

awg.write('clock:srate {}'.format(sampleRate))
awg.write('wlist:waveform:new "{}", {}'.format(name1, recordLength))
awg.write_binary_values('WLISt:WAVeform:DATA "{}",'.format(name1), sinusoid)

awg.write('wlist:waveform:new "{}", {}'.format(name2, recordLength))
awg.write_binary_values('WLISt:WAVeform:DATA "{}",'.format(name2), noisysinusoid)

awg.write('source1:casset:WAVeform "{}"'.format(name1))
awg.write('output1:state on')

awg.write('source2:casset:WAVeform "{}"'.format(name2))
awg.write('output2:state on')

awg.write('awgcontrol:run:immediate')

print(awg.query('system:error:all?'))
awg.close()
