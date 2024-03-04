Feature: SP-3833

	#Verify configured alarm for multiple devices in healthState UNKNOWN
	@XTP-30405
	Scenario: Configure alarm rule for healthState UNKNOWN
		Given a mid telescope
		Given an alarm handler
		Given an alarm handler is configured to raise an alarm when the <device1> <device2> healthState 
		When <device1> and <device2> remain in healthState UNKNOWN for long
		Then alarm for healthState UNKNOWN must be raised with UNACKNOWLEDGE state
		Examples:
		    |         device1                | device2                        | 
		    |ska_mid/tm_central/central_node | ska_mid/tm_subarray_node/1     |
