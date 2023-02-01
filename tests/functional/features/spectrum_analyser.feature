Feature: Spectrum Analyser

    @XTP-13599 @skip
    Scenario Outline: Test that a Spectrum Analyser can be configured to plot a trace
        Given the Spectrum Analyser is online
        And the Spectrum Analyser is initialised
        When the user sets the Spec Analyser start freq as <start_freq> Hz
        And the user sets the Spec Analyser stop freq as <stop_freq> Hz
        Then the Spec Analyser start freq is set to <start_freq> Hz
        And the Spec Analyser stop freq is set to <stop_freq> Hz

        Examples:
            | start_freq        | stop_freq |  
            | 25000000.0        | 75000000.0     |  
            | 50000000.0        | 200000000.0    |
