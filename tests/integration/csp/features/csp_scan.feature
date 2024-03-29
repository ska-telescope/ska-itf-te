@XTP-4769
Feature: Run a scan on CSP subarray


    @XTP-4771 @XTP-5537 @XTP-4769 @XTP-3324 @XTP-5573
    Scenario: Run a scan on csp subarray in mid
        Given a CSP subarray in READY state
        When I command it to scan for a given period
        Then the CSP subarray must be in the SCANNING state until finished

    @skip @XTP-16345
    Scenario: Abort Csp scanning
        Given an subarray busy scanning
        When I command it to Abort
        Then the subarray should go into an aborted state

