
#Remove configured TMC alarms using alarm handler configurator tool
@XTP-30175
Scenario: Remove TMC alarms
    Given a TMC
    Given an alarm handler
    Given TMC alarm is configured with tag <tag_name>
    When I remove configured TMC alarm tag <tag_name> using alarm configurator tool
    Then TMC alarm tag <tag_name> is removed successfully
    Examples:
    | tag_name                   |
    | subarraynode_obsstate_fault|