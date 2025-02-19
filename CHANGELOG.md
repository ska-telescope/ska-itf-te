# Version History

## Unreleased

## 25.6.1
* [AT-2586] - Fixed SKB-606 with updates of TMC

## 25.5.0
* [AT-2726] - Fixed SDP PVC patch Yaml file with correct labelling of PVC.

## 25.4.0
* [AT-2624] - Readthedocs YAML updates
* [AT-2586] - Improved Telescope Teardown procedure
* [AT-2649] - Parameterised more End-to-end Test variables
* [AT-2582] - Fixed zero-delay co-ordinates

## 25.3.0

* [AT-2487] - fixed pipeline dependency chain
* [AT-2487] - added two receptors - we now have four-receptor deployments available
* [AT-2306] - Telescope Teardown tool added, along with improved pipeline tooling
* [AT-2569] - Four-receptor e2e test in automated pipelines
* [MAP-229] & [MAP-212] - Validation of ADR-99 updates, MCS & Engineering Console version bumps and DishLMC upgrades validated
* [AT-2620] - Taranta upgrades
* [AT-2582] - (untested) Zero Delay Receptor layout pulled into CSPSubarrayLeafnode values file
* [SKB-707] - Added documentation related to testing
* [AT-2584] - (untested) FluxCD services added for SKA063
* [AT-2526] - Skipped failing alarmhandler tests and added SPFC deployment for DishLMC (POC)
* [AT-2533] - Vis receive script updates
* [AT-2502] - Upgraded deployment in ITF to four-receptor system with hardware enabled
* [AT-2387] - Gitlab pipeline fixes and improvements

## 24.4.1

* [AT-2350] - Updated Jupyter Notebook
* [BANG-635] - Added FluxCD Deployment mechanism for deploying DishLMC to VM and KDRA Dish SKA063 from release branch
* [SP-4666] - Linting fix
* [AT-2202] - Deployment steps link added to README

## 24.4.0

* [AT-2409] - Enabled EDA Deployment in staging environment
* [AT-2346] - Added optional SPFC deployment to pipelines
* [MAP-166] - Official Releases updated for TMC, CSP.LMC, DishLMC and E2E BDD test updated to accommodate these changes
* [AT-2311] - Updated Taranta Dashboards for major products; added Dish Dashboard updating script

## 24.3.1

* [AT-2391] - Updated engineering tools version to accomodate for non semver compliant version numbers in the dependency checker tool

## 24.3.0

* [AT-2367] - Updated Jupyter Notebooks to latest stable hash
* [AT-2307] - Manual E2E pipeline job testing the staging deployment on-demand and on a schedule, minor fixes and updates
* [AT-2359] - Added SPFC deployment in-the-loop for DishLMC namespaces, set to true for SKA063 namespace by default (but with no SPFRx HW), in the Mid ITF cluster
* [AT-2333] - Updated Engineering Tools image version
* [AT-2329] - Added SPFC to list of devices for exclusive-use management
* [AT-2249] - Added BDD Test for end-to-end signal chain verification via TMC, including upgrades, fixes and updates.

## 24.1.1

* [REL-1722] - fixed submodule URLs

## 24.1.0

* [AT-2270] - bumped SPFRx deployer version
* [AT-2268] - fixed SDP PVC deployment & destroy issue
* [STS-1128] - upgraded Makefiles - now with long-help

## 23.5.0

* [REL-1679] - Patched TMC, CSP.LMC & CBF.MCS with dev images used, downgraded CBF Engineering Console, Tango Archiver bump, Fixed EDA deployment

## 23.4.1

* [AT-2226] - Found a stable combination of software versions (and patches) which allow e2e telescope testing via TMC

## 23.4.1

* [SKB-471] - Improved consumption of nr_of_subarrays in pytests
* [AT-2213] - Bumped versions: talondx-console -> 0.3.2, csp-lmc-mid -> 0.23.1, tmc-mid -> 0.21.2, ska-ser-skallop -> 2.31.3
* [AT-2216] - PVC namespace set incorrectly for vis receive pods

## 23.4.0

* [AT-2213] - no longer removing failed deployments - this is a big risk
* [AT-2213] - Bumped DishLMC to 4.1.0 and use custom dishsimulators with speeds never seen before
* [AT-2213] - put back the TMC Dishleafnode patch image
* [AT-2213] - automated chart version update for Mid ITF chart

## 23.3.1

* [AT-2188] - upgraded DishLMC to 4.0.0
* [AT-2186] - Indicate CBF in-the-loop on Grafana and avoid deploying Engineering Console unless CBF is in-the-loop

## 23.3.0

* [MAP-102] - updated Mid CBF now allows 2 FSPs to be used, updated MCS and Eng Console, latest SDP, latest SPFRx TalonDx Console
* [AT-2109] - SUT configuration now with PBS names for Charts instead of chart-names
* [AT-2173] - Jupyter Notebooks submodule added
* [AT-2181] - TMC patch removed
* [AT-2181] - Various chart versions updated, SUT chart renamed
* [AT-2173] - Publishing DPD umpbrella chart
* [AT-2173] - Update Engineering Console image

## 23.2.1

* [AT-2139] - Added TMC Mid patch image and DishLMC upgrade for TrackTable delay fix (SKB-419).
  
## 23.2.0

* [AT-2122] - DPD is deployed with the correct PVC name and can therefore correctly access the shared data products volume
* [AT-2158] - Bumped mid-dish-spfrx-talondx-console version to 0.3.1
* [AT-2142] - ska-mid-cbf-engineering-console deployment is disabled by default and is only deployed when the CBF_HW_IN_THE_LOOP environment variable is set to true

## 23.1.1

* [AT-2130] - Bumped Taranta and TangoGQL versions to 2.10.2 and 1.4.3 respectively

## 23.1.0

* [AT-2127] - Added k8s-wait in dish-lmc deployment to wait for spfrx pods in the namespace to be ready
  [AT-2130] - Bumped Taranta and TangoGQL versions to 2.10.1 and 1.4.1 respectively
  [AT-2069] - Removed Test equipment deployments (moved to ska-mid-itf-environments repository)
  [AT-2077] - Fixed error in reading talondx console version in the dependency graph generated on the automated test reports page

## 23.0.1

* [AT-2115] - patched Engineering Tools to 0.9.1

## 23.0.0

* [REL-1564] - bumped to first major release for PI 23
* [AT-2111] - Patched TMC SDPSubarrayLeafnode image
* [AT-2111] - patched DishLMC image to Gitlab Registry version to use interim ICD patch

## 22.6.0

* [REL-1521] - rollback of ODA and first release of last PI22 Sprint

## 22.0.1

* [AT-2044] - Use engineering console version 0.10.6 to mitigate SKB-352.
