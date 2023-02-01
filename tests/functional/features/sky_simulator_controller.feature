@SP-2854
Feature: Sky Simulator components can be controlled remotely using Tango device server that communicates with Raspberry Pi using SCPI commands
	#Currently up to seven simple hardware devices can be switched ON/OFF remotely using GPIO control from a Raspberry Pi (RPi). This is already working, but access to the RPi is needed, which involves SSH connection and additional screens open. This leaves room for improvement.
	#
	#We can use the SCPI device simulators currently available in the SKA Test Equipment repository and instead of simulating a device we can potentially call simple GPIO commands as response to incoming SCPI commands. If the SCPI commands are simple enough, the Tango Device Servers are already available with which we can then control SCPI devices from Taranta / Jupyter Notebooks, and implementing these Device Servers should enable us to monitor and control the Sky Simulator components in similar ways as other Test Equipment.
	#
	#Implementing the SkySim Controller in a web server running on the Raspberry Pi that can be connected to using a TCP socket (which is how the current Device Servers connect to the Device Simulators), is then all that is needed to control the hardware from Tango UIs.
	#
	# 
	#
	#The Programmable Attenuator has a simple Telnet interface, that could potentially also be communicated with from the same Raspberry Pi web server. It has two commands: Set Attenuation, and Read Attenuation. These should be added to the same Sky Simulator Controller.
	#
	# 

	#Assert whether a RPi SCPI device simulator can receive SCPI commands and respond as expected
	#
	#So that we can develop the SkySim controller Tango device in the same way as the other Test Equipment Tango devices.
	#
	#This test should pass when executed against the real HW as well as (first) the SkySimControllerSimulator (a Simulator that runs alongside the Tango Device Servers in the same k8s cluster).
	@AT-319 @AT-318 @AT-317
	Scenario Outline: Test SkySimCtl can switch ON signal sources
		Given the SkySimController is online
		And the SkySimController is initialised (all signal sources OFF)
		When I switch on the <signal_source_name> # Get signal source names from @Ben.Lunsky
		Then the <signal_source_name> must be ON # SCPI field value (ON/OFF) should be translated to a Tango attribute (boolean)
		
		Examples:
		    
		    | signal_source_name            |
		    | "gaussian_noise_source"       |
		    | "programmable_attenuator"     |
		    | "correlated_noise_source"     |
		    | "h_channel"                   |
		    | "v_channel"                   |
		    | "uncorrelated_noise_sources"  |
		    | "band_1"                      |
		    | "band_2"                      |
		    | "band_3"                      |	

	#Test if, when asked its name, the Sky Simulator Controller responds as expected.
	@AT-320 @AT-318 @AT-317
	Scenario: Test SCPI device returns identity
		Given the SkySimController is online
		And the SkySimController is initialised (all signal sources OFF)
		When I ask its identity
		Then it responds "SkySimController"