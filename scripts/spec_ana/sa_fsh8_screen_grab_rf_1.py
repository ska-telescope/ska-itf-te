"""

This Python code transfer takes screenshot and transfers it from spectrum analyzer to the controller PC. 
Preconditions:
Author: R&S Customer Support
modified by: Vhuli , date: 18.03.2022
Before running, please always check that you have all libraries installed.
"""

from re import S
from RsInstrument import *
from time import time
import pyvisa_py
import pyvisa
import time
import socket

def sa_hcopy():
     
    SA_FSH8 = None
    try:
        # connecting via socket without using visa adjust the VISA Resources
        #Setting reset to True (default is False) resets your instrument. It is equivalent to calling the reset() method.
        #Setting id_query to True (default is True) checks, whether your instrument can be used with the RsInstrument module.
        #  "SelectVisa='socket'">>>Using RsInstrument without VISA for LAN Raw socket communication
        SA_FSH8 = RsInstrument('TCPIP::10.8.88.138::5555::SOCKET', False, False, "SelectVisa='socket'")
        SA_FSH8.opc_timeout = 3000  # Timeout for opc-synchronised operations
        SA_FSH8.instrument_status_checking = True  # Error check after each command
    except Exception as ex:
        print('Error initializing the instrument session:\n' + ex.args[0])
        exit()
    
    print(f'Device IDN: {SA_FSH8.idn_string}')
    print(f'Device Options: {",".join(SA_FSH8.instrument_options)}\n')

    #rth.clear_status()
    #rth.reset()
    ##set print to file
  
    file_path_SA_FSH8 = r'\Public\Screen Shots\test_capture1.png' # Instrument screenshoot file path
    #PC screenshoot file path(saved in googledrive)
    file_path_PC = r'/Volumes/GoogleDrive/My Drive/System ITF/Sotfware/Spetrum Analyzer/python/Test_Scripts/v1/test_capture1.png'
   
    ##  select file format
    SA_FSH8.write_str("HCOP:DEV:LANG PNG") 

    ## file path on instrument
    SA_FSH8.write_str(f"MMEM:NAME '{file_path_SA_FSH8}'")

    #create screenshot
    SA_FSH8.write_str_with_opc("HCOP:IMM") 

    #copy screenshoot from intrument to the pc
    SA_FSH8.read_file_from_instrument_to_pc(file_path_SA_FSH8, file_path_PC)
    
    SA_FSH8.close()
    #plt.show()


if __name__ == "__main__":
    sa_hcopy()