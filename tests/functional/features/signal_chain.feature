Feature: ITF Test Equipment testing flow integration

    @XTP-13587 @forked 
    Scenario Outline: Test connection between Signal Generator and Spectrum Analyser
        Given the Signal Generator is online
        And the Signal Generator is initialised
        And the Signal Generator RF output is OFF
        And the Spectrum Analyser is online
        And the Spectrum Analyser is initialised
        When the user specifies the Spectrum Analyser stop frequency as <frequency_stop> Hz
        And the user specifies the Spectrum Analyser start frequency as <frequency_start> Hz
        And the user specifies the Signal Generator frequency as <frequency> Hz
        And the user specifies the Signal Generator power as <power> dBm
        And the user turns the Signal Generator RF output ON
        Then the Spectrum Analyser peak frequency is approximately <frequency> Hz
        And the Spectrum Analyser peak power is no more than <power> dBm

        Examples:
            | frequency_start | frequency_stop |  frequency  | power |
            | 25000000.0      | 75000000.0     |  50000000.0 | -20.0 |
            | 50000000.0      | 200000000.0    | 100000000.0 | -10.0 |
