Feature: PVC is deployed with SUT

    Checks if PVC is deployed in SDP namespace along with SUT

Scenario: PVC deployment successful
    Given a kubernetes cluster deployment of the SUT which includes the SDP
    Then there should be a pvc in the SDP namespace