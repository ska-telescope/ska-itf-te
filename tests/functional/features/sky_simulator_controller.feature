Feature: Sky Simulator Controller 

    @AT-319 @forked 
    Scenario Outline: Test SkySimCtl can switch ON signal sources

Given the SkySimController is online
And the SkySimController is initialised (all signal sources OFF)
When I switch on the <signal_source_name> # Get signal source names from @Ben.Lunsky
Then the <signal_source_name> must be ON # SCPI field value (ON/OFF) should be translated to a Tango attribute (boolean)

Examples:
    | signal_source_name        |
    | "Gaussian_Noise_Source"   |
    | "Programmable_Attenuator" | # is this one of the pins?
    | "GPIO_3"                  |
    | "GPIO_4"                  |
    | "GPIO_5"                  |
    | "GPIO_6"                  |
    | "GPIO_7"                  |
