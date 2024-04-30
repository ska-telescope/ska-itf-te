Feature: SP-3833

	#Verify configured alarm for multiple devices in healthState UNKNOWN
	@XTP-30405
	Scenario Outline: Configure alarm rule for healthState UNKNOWN
		Given a mid telescope
		Given an alarm handler
		When an alarm handler is configured to raise an alarm when the <device1> <device2> healthState 
		Then Alarms are configured succesfully for <device1> and <device1>
		Examples:
		    |         device1                | device2                        | 
		    |ska_mid/tm_central/central_node | ska_mid/tm_subarray_node/1     |
