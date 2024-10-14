=================================
Purpose and general documentation
=================================

Purpose of the Mid ITF Tests repository
=======================================
This project contains tests, deployment infrastructure and Helm charts for the remote control software for the Mid ITF Test Equipment to be used to test the SKAO products as they arrive in the SKA MID ITF facility.
Test results are automatically uploaded to Jira using the Xray plugin. The test results can then be used for Requirement coverage reports.

Mid ITF Control Interface
=========================
Documentation on accessing the ITF Control Interface is maintained in Confluence, mainly under `Accessing ITF network based Test Equipment and SUT <https://confluence.skatelescope.org/x/cdY_Cw>`_. The System Under Test (SUT) as defined in this repository comprises most of the centrally deployed software products, and should not be confused with the SUT that is depicted in the block diagram showing the full SUT. The main difference is that the DishLMC, ODA, EDA and other items are deployed in namespaces (or clusters) separate from the one where the central monitoring and control software such as TMC, CSP.LMC, CBF.MCS, SDP, Taranta (Web GUI) and others are deployed.

DishLMC Integration at the Mid ITF
==================================
We use an OPC UA server in the K8s Cluster in the Mid ITF to simulate the Dish Structure (DS)for DishLMC integration. Details for connecting to the DS Simulator are available in `Confluence <https://confluence.skatelescope.org/x/Jz6KDQ>`_. For assistance, please reach out in `#team-itf-support <https://skao.slack.com/archives/C03PC2M2VGA>`_.

Data Product Dashboard
======================
The Data Product Dashboard for the integration deployment can be accessed.

Useful Links:

1. `Developer Portal Documentation <https://developer.skao.int/projects/ska-sdp-dataproduct-dashboard/en/latest/index.html>`_.
2. `Dashboard <https://k8s.miditf.internal.skao.int/ska-dpd/dashboard/>`_
3. `API <https://k8s.miditf.internal.skao.int/ska-dpd/api/>`_

Alarm Handler
=============

The Alarm Handler Solution is based on Elettra Alarm Handler provided by the Tango community. For more details see the User Guide.

Useful links:

1. `Alarm Handler User Guide <https://confluence.skatelescope.org/display/UD/Alarm+Handler+User+Guide>`_
2. `Alarm Handler Confurator <https://k8s.miditf.internal.skao.int/integration/alarm-configurator/>`_

Engineering Data Archiver (EDA)
===============================

The SKA EDA solution is based on HDB++ (Historical Data Base++), which is a standard archiver tool in Tango ecosystem used for archiving tango attributes. For more details see the user guide.

Useful links:

1. `EDA User Guide <https://confluence.skatelescope.org/display/UD/EDA+User+Guide>`_
2. `Configuration Page <https://k8s.miditf.internal.skao.int/integration/configurator/configuration-page>`_
3. `Archviewer <http://archviewer.integration.svc.miditf.internal.skao.int:8082>`_

==========
Deployment
==========

Deployment of the SUT
=====================
The deployment repository for the SKA Mid Software used to be Skampi. This has now been replaced by the machinery present in this repo.
The SUT is defined in the `ska-mid-itf-sut` chart and can be deployed using the following jobs:

1. `deploy-sut-on-demand` (manual): creates a short-lived deployment to a `ci-ska-mid-itf-$CI_COMMIT_REF_NAME` namespace. This is intended for testing and debugging and can be deployed from any branch.
2. `deploy-sut-integration` (manual): creates a long-lived deployment to the `integration` namespace. This can only be deployed from the main branch.
3. `deploy-sut-staging` (manual): creates a long-lived deployment to the `staging` namespace. This can only be deployed from the main branch.

Each of these deployment jobs has an associated `destroy-sut-*` job which will remove the deployment.

Deployment of the Dish LMC
==========================

There are 4 instances of the Dish LMC deployed from this project. Each instance is intended to exercise a different set of Dish LMC software simulators and external components.
The completed deployments will look as follows:

1. Dish LMC connected to only Dish LMC software simulators.
2. Dish LMC connected to CETC dish structure simulator and software simulators for SPFC and SPFRx.
3. Dish LMC connected to the physical SPFC and software simulators for Dish Structure and SPFRx.
4. Dish LMC connected to the physical SPFRx and software simulators for Dish Structure and SPFC.

Currently, only (2.) above is fully implemented.
This is deployed with the `deploy-dishlmc-ska001` job. When running in development branches, this will deploy into a `ci-dish-lmc-ska001-$BRANCH` namespace.
In the main branch, it is deployed to the `dish-lmc-ska001` namespace.
This deployment is triggered by deploying the dish structure simulator with the `deploy-ds-sim-ska001` job.
There is also a `redeploy-dishlmc-ska001` job which does an uninstall of the dish LMC prior to installing it and this is triggered by the `redeploy-ds-sim-ska001` job.
Both of these deployment jobs consume connection details exported by the dish structure simulator deployment jobs in order to be able to connect to the CETC dish structure simulator.
There is also an uninstall job, `uninstall-dishlmc-ska001`, which is used to remove the deployment.

At the moment, other the dish LMC instances can be deployed in the same way except that:

1. They do not require a deployment of the dish structure simulator.
2. They require the `deploy-dishlmc-ska001` job to have completed successfully.
3. They require the `deploy-aa05-dishes` job to have completed successfully. This is a the manual job in the `on_demand_itf_sut` stage.

Their uninstall jobs also require the `uninstall-aa05-dishes` job in the `on_demand_itf_sut` stage to have completed successfully.

Deployment of the Dish Structure Simulator
==========================================

The dish structure simulator can be deployed using the `deploy-ds-sim-ska001` job. It deploys to `ci-ds-sim-ska001-$BRANCH` namespace in development branches and to `ds-sim-ska001` in the main branch.
There is also a `redeploy-ds-sim-ska001` job which does an uninstall of the dish structure simulator prior to installing it.
The job exports connection details as an artifact which is consumed by the Dish LMC SKA001 deployment job.

Namespaces and pipeline definitions
===================================
In the present repository it is possible to deploy the charts in different namespaces in the ITF cluster. In specific it is possible to deploy in the following namespaces: 

.. table:: List of namespaces at February 2024
   :widths: auto

   ================================  ============================================================================================
     Name                              Description
   ================================  ============================================================================================
   ci-ska-mid-itf-commit-ref         Used for on-demand deployment of SUT and not persisted, optionally with hardware in the loop
   ci-dish-lmc-skaXXX-commit-ref     Used for on-demand deployment of Dish LMC controlled by on-demand SUT (TMC etc)
   ci-ska-mid-itf-dpd-commit-ref     Used for on-demand deployment of the Data Product Dashboard
   ci-ska-db-oda-commit-ref          Used for on-demand deployment of the ODA
   integration-dish-lmc-skaXXX       For testing TMC in integration namespace with Dish LMC in separate namespaces
   ds-sim-skaXXX                     For long-lived deployment of Dish Strcuture Simulator
   integration                       For long-lived deployment of the SUT but in general without hardware in the loop
   staging                           For demonstration purposes, a hardware-in-the-loop deployment from the main branch.
   staging-dish-lmc-skaXXX           For demonstration purposes, using TMC in staging namespace with Dish LMC in separate namespaces. Default with hardware-in-the-loop.
   ska-db-oda                        For long-lived deployment of the ODA
   ska-dpd                           For long-lived deployment of the Data Product Dashboard
   taranta                           For taranta backend deployment
   ================================  ============================================================================================

Please note that: 

* ``commit-ref`` represents the ``CI_COMMIT_REF_NAME`` environment variables of Gitlab (the branch or tag name for which project is built),
* ``skaXXX`` represents the dish identifier (i.e. ``ska001``, ``ska002``, etc.).

For each namespace, the definition of the pipeline used for deploying the various applications is available in the folder ``.gitlab/ci/za-itf/namespace``.

For example, the definition for the namespace ``ci-ska-mid-itf-commit-ref`` is available in ``.gitlab/ci/za-itf/ci-ska-mid-itf-commit-ref/.pipeline.yaml``. It is important to note that every ``.pipeline.yaml`` definition contains an hidden gitlab job as first item in order to highlight the environment variables (parameters) set for it. 

===================================
Demonstrations and Hardware testing
===================================
In order to enable exclusive usage of the hardware in the Mid ITF, the spookd ghost device plugin is used. This is a Kubernetes custom resource definition, with which arbitrary devices can be defined and made available to the cluster. The control software deployed in the cluster then claims these devices, and by using limits on each device, we can control where or how many instances of software that can actually control this hardware can be deployed. The limit is usually one, and the first one that was deployed while the hardware was available claims the resource. These settings are all done in the Helm Charts.

In the pipelines for the DishLMC and the SUT, we have flags that control whether or not hardware is to be controlled or not, with the deployed software. In the case of the SUT, we are currently (April 2024) concerned mainly with the Correlator hardware (TalonDx LRUs), whereas the DishLMC can or cannot claim and control the SPFRx by way of the spookd mechanism explained above.

TalonDx hardware-in-the-loop flags
==================================
Currently, only one flag is used to switch on only one TalonDx LRU. This will change soon. The flag is ``CBF_HW_IN_THE_LOOP`` and is set to ``false`` by default in the pipeline environment. When set to true, a set of complex ``make`` targets are required for downloading firmware artefacts, switching off and then on the hardware, etc. This is currently being modified but is still WIP.

SPFRx hardware-in-the-loop flags
================================
In each of the DishLMC pipeline jobs, the correct IP addressable hardware items are targeted for deployment `if` they need to be controlled. For each of the pipeline jobs, the flag ``SPFRX_IN_THE_LOOP`` should can be set, or it can be set globally for the pipeline, in which case all instances of the DishLMC will have hardware enabled. This flag is also set to ``false`` by default.

We mainly have three use cases for hardware-in-the-loop choices:

Feature testing and development branches
========================================
These branches can typically contain hardware-in-the-loop if necessary, but this is optional. Flags listed above should be set as per requirement.

Integration namespace (main branch)
========================================
This deployment should always be without hardware-in-the-loop, as multiple Jupyter Notebooks may at any given time aim to command or control the SUT in that namespace.

Staging namespace (main branch)
========================================
This is a special, non-long-living namespace, with typically hardware-in-the-loop deployments by default. The namespace must be destroyed after demonstrations, in order for others to be able to work against branched deployments instead.

**NOTE**
In all cases where hardware-in-the-loop tests are to be done, it should be announced beforehand in the [#team-mid-itf-support](https://skao.slack.com/archives/C03PC2M2VGA) Slack channel that the hardware is to be used.

Other subsystems in the loop
============================
DishLMC can also be controlled with the flag ``DISH_LMC_IN_THE_LOOP``, similarly to how the deployments for hardware-in-the-loop are controlled. By default, the DishLMC is mocked out in the ``integration`` namespace, by the TMC.

***************
Automated tests
***************
This repository contains end-to-end BDD tests for verifying the full signal chain which are executed within pipeline jobs targeted at ci- and staging namespaces in the mid-itf cluster. 

End-to-end testing via TMC - Software only
==========================================
Software only end-to-end tests are run in the k8s-test-runner pipeline job each time a change is made. Test execution reports are uploaded against the AT-2305 Jira ticket when the test is run from the main pipeline.

End-to-end testing via TMC - With hardware in the loop
======================================================
End-to-end tests are executed with hardware in the loop through on-demand pipeline jobs against the staging namespace. Hardware in the loop tests are also executed on a cadence through scheduled pipelines which trigger the on-demand hardware in the loop test jobs which execute against the staging namespace.
Scheduled hardware in the loop test jobs execute against the staging namespace daily at 03h00 SAST. Test execution reports are uploaded against the AT-2349 Jira ticket when the test is run from the main pipeline..

The test-end-to-end-staging pipeline job in the test stage is used to execute the hardware in the loop tests on demand. This job is available as an on-demand job in all pipelines with source push and merge_request_event. All tests within the tests/integration/tmc folder that have been marked using the hw_in_the_loop pytest marker will be executed by this job.
To view the configuration of the system deployed in the staging namespace, view the pipeline logs. This job assumes the following:
1. The telescope software has been successfully deployed with hardware in the loop into the staging namespace.
2. The TMC central node telescopeState is OFF.

The test-end-to-end-staging can be triggered to run automatically by setting the EXECUTE_STAGING_E2E_WITH_HW pipeline variable to "true"