"""
@author: Monde 
@Date: 05-04-2022
@Affiliation: Test Engineer
@Functional Description: 
    1. This script plots a trace in amplitude vs frequency from a CSV file
    2. Where it applies SA denotes Spectrum Analyzer 
    
@Notes: 
    1. This script was written for the FSH8 Spectrum Analyzer. Raw ethernet socket communication is used
        and thus VISA library/installation is not required
    2. This script uses scpi protocol for the automatic test equipment intended

@Revision: 1

"""
import socket
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# --------------Connection Settings-------------------
SA_HOST = '10.8.88.138'      # fsh8 spectrum analyzer IP
SA_PORT = 5555               # fsh8 spectrum analyzer port 18? 23?
address = (SA_HOST, SA_PORT)

#-----------------------------------------------------------
# ----------------Initialization of Variables---------------    
DEFAULT_TIMEOUT = 1         # Default socket timeout
recdur = 10                 # Time in seconds to find maxhold peaks

# ---------------------------------------------------------

class sa_sock(socket.socket):
    def sa_connect(self,address,default_timeout = 1,default_buffer = 1024,short_delay = 0.1,long_delay = 1):
        """ Establish socket connect connection.

        This function:
            - Establishes a socket connection to the Signal Generator. Uses address (Including Port Number) as an argument.
            - Performs a reset on the unit and sets the fixed frequency generator mode. 
            - Sets the Display to On in Remote mode
        @params 
            specAddress          : specHOST str, specPORT int
            default_timeout     : int timeout for waiting to establish connection
            long_delay          : int
            short_delay         : int
            default_buffer      : int
        """
        self.connect(address)                                
        self.settimeout(default_timeout)
        self.delay_long_s = long_delay
        self.delay_short_s = short_delay
        self.default_buffer = default_buffer
        rx_str = self.sa_requestdata('*IDN?')
        print('Connected to: %s \n'%rx_str)
        self.sa_sendcmd('*CLS')                                     
        self.sa_sendcmd('*RST')
        self.sa_sendcmd('INST:SEL SAN')
        self.sa_sendcmd('SYST:DISP:UPD ON')
        time.sleep(short_delay)

    def sa_dumpdata(self):
        """

        This function receives and displays the data after a query command
        @params:
            command  : string    
        """
        while True:
            try:
                dump_str = self.recv(self.default_buffer)
                print('Dumping buffer data: %s'%dump_str)
            except socket.timeout:
                break

    def sa_sendcmd(self,command_str):
        """
        
        This function sends the command and adds \n at the end of any commands 
            sent to the test device
        @params command  : string    
        """
        self.sendall(bytes(command_str, encoding='utf8') + b'\n')
    
    def sa_requestdata(self,request_str,response_buffer = 'default',timeout_max = 20):
        """

        This function requests and reads the command to and from the test device
        @params command  : string
        """ 
        if type(response_buffer) == str:
            response_buffer = self.default_buffer
            self.sa_dumpdata()                                         # Cleanup the receive buffer
            self.sa_sendcmd(request_str)                               # Send the request
            return_str = b''                                           # Initialize Rx buffer - b' for bytes init
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
                    if return_str.endswith(b'\n'):                      # Test to see if end of line has been reached, i.e. all the data Rx, - b' for bytes
                        return return_str[:-1]                          

    def traceget(self):
        """Get trace by csv.
        
        This function reads the power and sweep points to plot the trace
        from the csv.
        @params:
            None 
        """
        self.sa_sendcmd('INIT:CONT ON')                    
        time.sleep(int(recdur))                                                        
        self.sa_sendcmd('INIT:CONT OFF')                    
        self.sa_sendcmd('FORM:DATA ASC')                     
        TraceData=self.sa_requestdata('TRAC:DATA? TRACE1')      
        NoSweepPoints = int(self.sa_requestdata('SWE:POIN?'))      
        print(f"NoSweepPoints is {NoSweepPoints}")              
        TraceData = str(TraceData)
        print(f"The type of TraceData is {type(TraceData)} and TraceData is {TraceData}")
        CSVTraceData=TraceData.split(",")               
        CSVTraceData = [s.replace("b'", '') for s in CSVTraceData]
        CSVTraceData = [s.replace("'", '') for s in CSVTraceData]
        print(f"CSVTraceData is {CSVTraceData}.")
        CSVTraceData_lis=[]
        for s in CSVTraceData:
            CSVTraceData_flo = round(float(s),ndigits=2) 
            CSVTraceData_lis.append(CSVTraceData_flo)
        CSVTraceData_list = [str(x) for x in CSVTraceData_lis]   
        freq_span = self.sa_requestdata("FREQ:SPAN?")  
        freq_span = float(freq_span.decode('utf-8'))   
        freq_span = freq_span/1e6
        CSVTracePoints = float(freq_span / NoSweepPoints)
        CSVTracePoints = round(CSVTracePoints,ndigits=2)
        CSVTracePoints_list = []
        i = 0
        while i < NoSweepPoints:                            
            CSVTracePoints_list.append(i * CSVTracePoints) 
            i = i + 1

        # Write csv file
        file = open (r'./TraceFile.csv', 'w')          # Open File for writing
        file.write("Frequency in kHz;Power in dBm\n")  # Write the headline
        x=0                                            # Set counter to 0 as touple does not begin with 1
        while x < int(NoSweepPoints):                  # Perform loop until all sweep points are covered
            file.write(str(CSVTracePoints_list[x]))    # Write amplitude measurement data
            file.write(";")                            # Add semicolon as CSV separator
            file.write(CSVTraceData_list[x])           # Write frequency data
            file.write("\n")                           # Add a new line control character
            x=x+1                                      # Increment counter
        file.close()

        # Plot the trace
        x_axis = CSVTracePoints_list
        y_axis = CSVTraceData_lis
        plt.plot(x_axis, y_axis)
        plt.xlabel('Frequency in MHz')
        plt.ylabel('Power in dBm')
        plt.title('Trace 1 Response')
        plt.show()
        
if __name__ == '__main__':
    print("/------Setup spectrum analyser---------/\n")
    a = sa_sock()
    a.sa_connect((SA_HOST,SA_PORT))
    a.traceget()

print("Program ended successfully")