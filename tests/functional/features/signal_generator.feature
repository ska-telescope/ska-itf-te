Feature: Signal Generator 

    @XTP-7690 @forked @skip
    Scenario Outline: Test a Signal Generator frequency and power can be set
        Given the Signal Generator is online
        And the Signal Generator is initialised
        When the user specifies the Signal Generator frequency as <frequency> Hz 
        And the user specifies the Signal Generator power as <power> dBm
        Then the Signal Generator frequency is set as <frequency> 
        And the Signal Generator power is set as <power>

        Examples:
            |frequency   | power  |
            |50000000    | -20    |
            |100000000   | -10    |
   
    @XTP-9312 @forked @skip
    Scenario Outline: Test a Signal Generator frequency can not be set with a negative value
        Given the Signal Generator is online
        And the Signal Generator is initialised
        When the user specifies the Signal Generator frequency as <frequency> Hz 
        Then the Signal Generator returns an error message 
        
        Examples:
            |frequency   | 
            |-50000000   |

    @XTP-9042 @forked @skip
    Scenario: Test a Signal Generator output can be turned ON
        Given the Signal Generator is online
        And the Signal Generator is initialised
        And the Signal Generator RF Output is OFF
        When the user turns the Signal Generator RF Output ON
        Then the Signal Generator RF Output field is set to ON 


    @XTP-9041 @forked @skip
    Scenario: Test a Signal Generator output can be turned OFF
        Given the Signal Generator is online
        And the Signal Generator is initialised
        And the Signal Generator RF Output is ON
        When the user turns the Signal Generator RF Output OFF
        Then the Signal Generator RF Output field is set to OFF

    
