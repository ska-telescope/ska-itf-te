# -*- coding: utf-8 -*-
"""
@author: Monde: 
        Date: 24-03-2022
        Affiliation: SKAO Test Engineer
        Functional Description: 
        This script generates discrete frequencies from 100 MHz to 2.3 GHz at 100 MHz steps        
"""

from re import S
import time
import socket

# The script uses raw ethernet socket communication, and thus VISA library/installation is not required

# --------------Initialization of Variables---
Power = 0.0             # Start RefLev                              
Freq = 900e3            # Minimum 100kHz     
default_timeout = 1     # Default socket timeout
rf_state = 0            # Default RF Out state
fstart = 0.9            # 
fstop = 3000
# --------------------------------------------
# -----------Global Variables-----------------
dump_str = ''

# -----------Connection Settings--------------
sigPORT = 5025             # default SMB R&S port 
sigHOST = '10.8.88.166'    # smb100a signal generator IP
specPORT = 5555            # fsh8 port
specHOST = '10.8.88.138'   # fsh8 signal generator IP
#---------------------------------------------

sigAddress = (sigHOST, sigPORT)
specAddress = (specHOST, specPORT)

class sig_sock(socket.socket):
    def sig_gen_connect(self,sigAddress,default_timeout = 1,default_buffer = 1024,short_delay = 0.1,long_delay = 1):
#       A function to connect to the Signal Generator. Uses address (Including Port Number) as an argument.
#       Performs a reset on the unit and sets to Spectrum Analyser mode. Also sets the Display to On in Remote mode
        try:
            self.connect(sigAddress)                                
            self.settimeout(default_timeout)
            self.delay_long_s = long_delay
            self.delay_short_s = short_delay
            self.default_buffer = default_buffer
            rx_str = self.sa_requestdata('*IDN?')
            print('Connected to: %s'%rx_str)
            self.sa_sendcmd('*CLS')                                     
            self.sa_sendcmd('*RST')
            #self.sa_sendcmd('INST:SEL SAN')
            self.sa_sendcmd('SYST:DISP:UPD ON')
            time.sleep(short_delay)
        except Exception as e:
            print(e,f"Check to see if the port number is {sigPORT}")

    def sa_dumpdata(self):
        while True:
            try:
                dump_str = self.recv(self.default_buffer)
                print('Dumping buffer data: %s'%dump_str)
            except socket.timeout:
                break

    def sa_sendcmd(self,command_str):
        """
        This function adds \n at the end of any commands sent to the test device
        @params command  : string    
        """
        self.sendall(bytes(command_str, encoding='utf8'))
        self.sendall(bytes('\n', encoding='utf8'))

    def sa_requestdata(self,request_str,response_buffer = 'default',timeout_max = 20):
        """
        This function requests and reads the command to and from the test device
        @params command  : string    
        """ 
        if type(response_buffer) == str:
            response_buffer = self.default_buffer
        self.sa_dumpdata()                                         # Cleanup the receive buffer
        self.sa_sendcmd(request_str)                               # Send the request
        return_str = b''                                           # Initialize Rx buffer
        time_start = time.time()                                   # Get the start time
        while True:
            time.sleep(self.delay_short_s)                         # Introduce a short delay
            try:
                return_str += self.recv(response_buffer)           # Attempt to read the buffer
            except socket.timeout:
                if (time.time()-time_start) > timeout_max:
                       raise StopIteration('No data received from instrument') 
                else:
                    time.sleep(self.delay_short_s)                  # No response, keep waiting
            else:
                if return_str.endswith(b'\n'):                      # Test to see if end of line has been reached, i.e. all the data Rx
                    return return_str[:-1] 

    def setRFOut(self, rf_state):
        """
        This function sets the RF Output ON or OFF
        @pa
        rams rf_state  : bool    [On/Off]
        """
        self.sa_sendcmd(f'OUTP {rf_state}')                         # Set RF Output
        dump_str = self.sa_requestdata('OUTP?')                     # Query RF Output
        print(f'dump_str is {dump_str}')                            # Print received data 
        if dump_str.decode('utf8')=='1\n':                          # Decode received data
            print("RF Output On")
        else: print("RF Output Off")

    def setSigGenPower(self, power):
        """
        This function sets the power of the signal generator
        @param  Power: float    [dBm]
        """
        self.sa_sendcmd(f'POW {power}')
        data = self.sa_requestdata('POW?')
        print(f"Sig gen power = {data} dBm")

    def setSigGenFreq(self,Freq):
        """
        This function sets the frequency of the signal generator
        @param  Freq: float [MHz]
        """
        self.sa_sendcmd(f'FREQ {Freq}')
        data = self.sa_requestdata('FREQ?')
        print(f"Sig gen frequency = {(data/1e6)} MHz")
        
    def sigGenFreqs(self):
        """
        This function generates discrete frequencies from 100 MHz
        to 2.3 GHz at 100 MHz steps
        @param  none
        """
        self.sa_sendcmd('FREQ:MODE FIX')                    # Set frequency mode to fixed
        cur_freq = 0                                        # Initialize freq container     
        for i in range(1,24):                               # Offset to 1, freq cannot be 0 MHz
            time.sleep(3)                                   # Delay 3 secs for visibility
            cur_freq = (100*i)                              # Compute and iterate frequency multiples
            cur_freq_str = str(cur_freq) + 'MHz'            # Convert frequency to string
            self.sa_sendcmd(f'FREQ {cur_freq_str}')         # Set frequency 
            print(f"Set Frequency {cur_freq_str}...")       # Print current frequency
            print(i)

    def closeGenSock(self):
        self.close()
        print('Signal Generator socket Disconnected')

# ---------------------------------------------------
# End of Signal Generator class
# ---------------------------------------------------

#%%   
# Main program
# -----------------------
if __name__ == '__main__':
    print("/------Setup signal generator---------/")
    sigGen = sig_sock()                                 # Call main class
    sigGen.sig_gen_connect((sigHOST,sigPORT))           # Connect Sig Gen remotely
    time.sleep(1)                                       # Delay 1 sec
    sigGen.setRFOut('ON')                               # Activate Output signal                                
    time.sleep(1)                                       # Delay 1 sec
    sigGen.sigGenFreqs()                                # Activate frequency generator
    time.sleep(1)                                       # Delay 1 sec
    sigGen.setSigGenPower(-30)                          # Sets Sig Gen power (put no units here)
    time.sleep(1)                                       # Delay 1 sec
    sigGen.closeGenSock()                               # Close socket
    print("/------End of Setup signal generator---------/")
