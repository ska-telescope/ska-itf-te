# Version History

## Unreleased

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
