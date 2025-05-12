# Version History

## Unreleased
* [AT-3002]
  * Upgraded CBF MCS to 1.3.0 and SDP to 1.1.2
  * Added exception handling for cspmasterleafnode.dishvccconfig check
  * Removed override of global.dish_suffix in SUT values
* [AT-3033]
  * Updated TMC version to 1.0.0.git s

## 26.3.0
* [AT-2966]
  * Modified Spookd Values to move resources to cloud04
* [AT-2880]
  * End-to-end test improvements
* [AT-2925]
  * Upgraded Taranta, Tango Base, Tango Util charts
* [SDR-1415]
  * New TMC dashboards
* [AT-2682]
  * Check CBF ON state in end-to-end test
* [AT-2874]
  * Use SPFC deployer v0.2.3 and include SKA036 archiver config
* [AT-2880]
  * Store SUT and Dish Kubernetes pod logs as artifacts during SW and HW test runs
  * Command configuration files stored as artifacts during SW and HW test runs
  * Use DISH_IDS environment variable to set receptors in E2E BDD tests
* [AT-2938]
  * Add ska-mid-testing chart containing Kubernetes resources which enable E2E testing in the KAPB

## 26.1.2
* [SKB-850]
  * Re-enable taranta

## 26.1.1
* [AT-2912]
  * Added ska-mid-cbf-tdc-tmleafnode chart to enable CBF verification tests. Disabled by default.
* [AT-2917]
  * Upgraded CSP to v1.0.1

## 26.1.0
* [AT-2906]
  * TMC name changes (ADR-9)
  * dish leafnode naming fixes (ADR-9)
  * alarm rules in tests with new names (ADR-9)
  * Upgraded TMC
  * Upgraded CBF.MCS and CBF.EC
  * Upgraded Archiver
  * Disabled Taranta (temporary - SKB-850)
  * Disabled TangoGQL (temporary - SKB-850)
  * Disabled CIA (temporary - SKB-850)
  * Disabled all tests except end2end test until name changes are incorporated into Skallop (ADR-9)
* [AT-2897]
  * Upgraded Telescope Model to work with latest product versions

## 26.0.0
* [AT-2856]
  * upgraded and pulled newly-named DPD chart to 0.10.0
* [AT-2811]
  * no longer creating our own PVC in DPD namespace - manage via Helm only
* [AT-2855]
  * upgraded CSP.LMC to 1.0.0 and removed DishLMC custom image override
* [AT-2843]
  * store command config strings as CI job artefacts

## 25.6.3
* [AT-2354]
  * Output links to Grafana dashboards and Kibana logs for the SUT namespace whenever integration-test is called
* [AT-2611]
  * Updated Ansible scripts with most recent users of the ITF jump host and corrected SPFRx network configurations
* [AT-2766]
  * SKB-606 resolutions:
                Bumped TMC to v0.25.0;
                Bumped SPFRx deployer to v0.5.0;
                Bumped DishLMC chart to v7.0.0;
                Added DishLMC patch image version 7.0.0-dev.ca11be44a (temporary workaroud);
                Removed CSP SubarrayLeafnode patch image (workaround)

* [AT-2805]
  * Gitlab e2e test job targets one specific test
* [AT-2612]
  * PlantUML Sequence diagrammes generated while using Notebooks and during CI pipeline tests, saved with artefacts
* [AT-2726]
  * Added pod to SDP namespace to check if PVC is available;
              also moved PVC patch info

## 25.6.2
* [AT-2647]
  * Split end-to-end tests - ON and OFF commands now separated from Observation sequences

## 25.6.1
* [REL-1963]
  * fixed non-functional deployment of MultiDB Taranta

## 25.6.0
* [AT-2756]
  * updated Tango Util & Tango Base charts
* [AT-2584]
  * MultiDB Taranta support

## 25.5.0
* [AT-2726]
  * Fixed SDP PVC patch Yaml file with correct labelling of PVC.

## 25.4.0
* [AT-2624]
  * Readthedocs YAML updates
* [AT-2586]
  * Improved Telescope Teardown procedure
* [AT-2649]
  * Parameterised more End-to-end Test variables
* [AT-2582]
  * Fixed zero-delay co-ordinates

## 25.3.0

* [AT-2487]
  * fixed pipeline dependency chain
* [AT-2487]
  * added two receptors - we now have four-receptor deployments available
* [AT-2306]
  * Telescope Teardown tool added, along with improved pipeline tooling
* [AT-2569]
  * Four-receptor e2e test in automated pipelines
* [MAP-229] & [MAP-212]
  * Validation of ADR-99 updates, MCS & Engineering Console version bumps and DishLMC upgrades validated
* [AT-2620]
  * Taranta upgrades
* [AT-2582]
  * (untested) Zero Delay Receptor layout pulled into CSPSubarrayLeafnode values file
* [SKB-707]
  * Added documentation related to testing
* [AT-2584]
  * (untested) FluxCD services added for SKA063
* [AT-2526]
  * Skipped failing alarmhandler tests and added SPFC deployment for DishLMC (POC)
* [AT-2533]
  * Vis receive script updates
* [AT-2502]
  * Upgraded deployment in ITF to four-receptor system with hardware enabled
* [AT-2387]
  * Gitlab pipeline fixes and improvements

## 24.4.1

* [AT-2350]
  * Updated Jupyter Notebook
* [BANG-635]
  * Added FluxCD Deployment mechanism for deploying DishLMC to VM and KDRA Dish SKA063 from release branch
* [SP-4666]
  * Linting fix
* [AT-2202]
  * Deployment steps link added to README

## 24.4.0

* [AT-2409]
  * Enabled EDA Deployment in staging environment
* [AT-2346]
  * Added optional SPFC deployment to pipelines
* [MAP-166]
  * Official Releases updated for TMC, CSP.LMC, DishLMC and E2E BDD test updated to accommodate these changes
* [AT-2311]
  * Updated Taranta Dashboards for major products; added Dish Dashboard updating script

## 24.3.1

* [AT-2391]
  * Updated engineering tools version to accomodate for non semver compliant version numbers in the dependency checker tool

## 24.3.0

* [AT-2367]
  * Updated Jupyter Notebooks to latest stable hash
* [AT-2307]
  * Manual E2E pipeline job testing the staging deployment on-demand and on a schedule, minor fixes and updates
* [AT-2359]
  * Added SPFC deployment in-the-loop for DishLMC namespaces, set to true for SKA063 namespace by default (but with no SPFRx HW), in the Mid ITF cluster
* [AT-2333]
  * Updated Engineering Tools image version
* [AT-2329]
  * Added SPFC to list of devices for exclusive-use management
* [AT-2249]
  * Added BDD Test for end-to-end signal chain verification via TMC, including upgrades, fixes and updates.

## 24.1.1

* [REL-1722]
  * fixed submodule URLs

## 24.1.0

* [AT-2270]
  * bumped SPFRx deployer version
* [AT-2268]
  * fixed SDP PVC deployment & destroy issue
* [STS-1128]
  * upgraded Makefiles - now with long-help

## 23.5.0

* [REL-1679]
  * Patched TMC, CSP.LMC & CBF.MCS with dev images used, downgraded CBF Engineering Console, Tango Archiver bump, Fixed EDA deployment

## 23.4.1

* [AT-2226]
  * Found a stable combination of software versions (and patches) which allow e2e telescope testing via TMC

## 23.4.1

* [SKB-471]
  * Improved consumption of nr_of_subarrays in pytests
* [AT-2213]
  * Bumped versions: talondx-console -> 0.3.2, csp-lmc-mid -> 0.23.1, tmc-mid -> 0.21.2, ska-ser-skallop -> 2.31.3
* [AT-2216]
  * PVC namespace set incorrectly for vis receive pods

## 23.4.0

* [AT-2213]
  * no longer removing failed deployments - this is a big risk
* [AT-2213]
  * Bumped DishLMC to 4.1.0 and use custom dishsimulators with speeds never seen before
* [AT-2213]
  * put back the TMC Dishleafnode patch image
* [AT-2213]
  * automated chart version update for Mid ITF chart

## 23.3.1

* [AT-2188]
  * upgraded DishLMC to 4.0.0
* [AT-2186]
  * Indicate CBF in-the-loop on Grafana and avoid deploying Engineering Console unless CBF is in-the-loop

## 23.3.0

* [MAP-102]
  * updated Mid CBF now allows 2 FSPs to be used, updated MCS and Eng Console, latest SDP, latest SPFRx TalonDx Console
* [AT-2109]
  * SUT configuration now with PBS names for Charts instead of chart-names
* [AT-2173]
  * Jupyter Notebooks submodule added
* [AT-2181]
  * TMC patch removed
* [AT-2181]
  * Various chart versions updated, SUT chart renamed
* [AT-2173]
  * Publishing DPD umpbrella chart
* [AT-2173]
  * Update Engineering Console image

## 23.2.1

* [AT-2139]
  * Added TMC Mid patch image and DishLMC upgrade for TrackTable delay fix (SKB-419).
  
## 23.2.0

* [AT-2122]
  * DPD is deployed with the correct PVC name and can therefore correctly access the shared data products volume
* [AT-2158]
  * Bumped mid-dish-spfrx-talondx-console version to 0.3.1
* [AT-2142]
  * ska-mid-cbf-engineering-console deployment is disabled by default and is only deployed when the CBF_HW_IN_THE_LOOP environment variable is set to true

## 23.1.1

* [AT-2130]
  * Bumped Taranta and TangoGQL versions to 2.10.2 and 1.4.3 respectively

## 23.1.0

* [AT-2127]
  * Added k8s-wait in dish-lmc deployment to wait for spfrx pods in the namespace to be ready
  [AT-2130]
  * Bumped Taranta and TangoGQL versions to 2.10.1 and 1.4.1 respectively
  [AT-2069]
  * Removed Test equipment deployments (moved to ska-mid-itf-environments repository)
  [AT-2077]
  * Fixed error in reading talondx console version in the dependency graph generated on the automated test reports page

## 23.0.1

* [AT-2115]
  * patched Engineering Tools to 0.9.1

## 23.0.0

* [REL-1564]
  * bumped to first major release for PI 23
* [AT-2111]
  * Patched TMC SDPSubarrayLeafnode image
* [AT-2111]
  * patched DishLMC image to Gitlab Registry version to use interim ICD patch

## 22.6.0

* [REL-1521]
  * rollback of ODA and first release of last PI22 Sprint

## 22.0.1

* [AT-2044]
  * Use engineering console version 0.10.6 to mitigate SKB-352.
