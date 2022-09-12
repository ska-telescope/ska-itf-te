
# Signal Generator Commands

SGCmds = {
    # Common commands
    'reset-device': '*RST', 
    'device-id': '*IDN',
    'oper-complete': '*OPC',
    'clear-status': '*CLS',

    # Frequency Commands
    'start-freq': 'SOUR:FREQ:STAR',         # pass start frequency e.g. SOUR:FREQ:STAR 100e6 
    'stop-freq': 'SOUR:FREQ:STOP',          # pass stop frequency e.g. SOUR:FREQ:STOP 2e9 Hz
    'step-freq': 'SOUR:FREQ:STEP',           # pass step frequency e.g. SOUR:FREQ:STEP 100e6 
    'current-freq': 'FREQ',                  # pass single FREQ value e.g. FREQ 2e9 Hz
    'cent-freq': 'FREQ:CENT',                # pass center freq FREQ:CENT {centFreq} Hz 
    'span-freq': 'FREQ:SPAN',                # pass span freq e.g. FREQ:SPAN {span} Hz
    'freq-mode': 'SOUR:FREQ:MODE',           # pass freq mode e.g. SOUR:FREQ:MODE SWE

    # Sweep Settings Commands
    'sweep-freq-mode': 'SWE:FREQ:MODE',      # pass sweep mode e.g. SWE:FREQ:MODE AUTO
    
    'sweep-freq-spac-conf': 'SWE:FREQ:SPAC', # pass sweep freq spacing e.g. SWE:FREQ:SPAC LIN
    'sweep-freq-step': 'SWE:FREQ:STEP:LIN',  # pass sweep step freq e.g. SWE:FREQ:STEP:LIN {step_freq}
    'sweep-freq-dwell': 'SWE:FREQ:DWEL',     # pass sweep dwell time SWE:FREQ:DWEL {dwel_time}
    'sweep-freq-trig': 'TRIG:FSW:SOUR',      # pass freq sweep trig e.g. TRIG:FSW:SOUR SING
    'sweep-freq-exec': 'SWE:FREQ:EXEC', # no paramater passed

    # RF 
    'rf-state': 'OUTP',

    # Power
    'power': 'POW',
    'set_start_pow': 'SOUR:POW:STAR',

}

# Spectrum Analyzer Commands

SACmds = {
    # Common commands
    'reset-device': '*RST', 
    'device-id': '*IDN',
    'oper-complete': '*OPC',
    'clear-status': '*CLS',

    # Frequency Commands
    'start-freq': ':FREQ:STAR',
    'stop-freq': ':FREQ:STOP',

    # Bandwidth Commands
    'res-bw': 'BAND:RES',      # pass rbw value e.g. BAND:RES 30e3
    'vid-bw': 'BAND:VID',      # pass rbw value e.g. BAND:VID 30e3 
    'rbw-auto': 'BAND:RES:AUTO',      # pass rbw value e.g. BAND:RES:AUTO off
    'vbw-auto': 'BAND:VID:AUTO',      # pass rbw value e.g. BAND:VID:AUTO off 

    # Amplitude Commands
    'ref-level': 'DISP:WIND:TRAC:Y:SCAL:RLEV',  # pass reflevel value e.g. DISP:WIND:TRAC:Y:SCAL:RLEV -30
    
    # Power Commands
    'att-level': 'POW:RF:ATT',                      # pass atten. level value e.g. POW:RF:ATT 10 
    
    # Sweep Commands
    'sweep-points': 'DISP:POIN',
    'sing-sweep-state': 'INIT:CONT',     # pass single sweep state e.g. INIT:CONT OFF

    # System Settings Commands
    'device-mode': 'MODE',                  # pass device mode e.g. MODE SPEC for spectrum analyzer

    # Trace Commands
    'trace': 'TRACE',                       # read trace, no param require 
    'trace-data': 'TRACE:DATA',             # pass trace no. parameter e.g. TRACE:DATA? 1
    'trace1-state': 'DISP:TRAC1',           # pass trace no. and state e.g. DISP:TRAC1 ON
    'trace1-mode': 'TRACE1:TYPE',           # pass trace mode e.g. TRACE1:TYPE MAX
    'max-hold-state': 'MAXH:STAT',          # pass maxhold state parameter e.g. MAXH:STAT ON
    
    # Detector commands
    'det-auto-state': 'DET:AUTO',           # pass ON or OFF e.g. DET:AUTO OFF
    'det-mode': 'DET',                      # pass APE, RMS e.g. DET APE      

    # Data commands
    'data-format': 'FORM:DATA',             # pass data format mode e.g.FORM:DATA ASC
    
}
