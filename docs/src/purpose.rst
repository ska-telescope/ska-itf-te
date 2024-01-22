=================================
Purpose and general documentation
=================================

Purpose of the Mid ITF Tests repository
=======================================
This project contains tests, deployment infrastructure and Helm charts for the remote control software for the Mid ITF Test Equipment to be used to test the SKAO products as they arrive in the SKA MID ITF facility. 
Test results are automatically uploaded to Jira using the Xray plugin. The test results can then be used for Requirement coverage reports.

Mid ITF Control Interface
=========================
Documentation on accessing the ITF Control Interface is maintained in Confluence, mainly under `Accessing ITF network based Test Equipment and SUT <https://confluence.skatelescope.org/x/cdY_Cw>`_.

DishLMC Integration at the Mid ITF
==================================
We use an OPC UA server in the K8s Cluster in the Mid ITF to simulate the Dish Structure (DS)for DishLMC integration. Details for connecting to the DS Simulator are available in `Confluence <https://confluence.skatelescope.org/x/Jz6KDQ>`_. For assistance, please reach out in `#team-itf-support <https://skao.slack.com/archives/C03PC2M2VGA>`_.

Spectrum Analyser File Access
=============================
The Ansritsu MS2090A Spectrum Analyser in the ITF hosts an FTP server. This allows users to access recordings made on the device remotely. In order to make this access more user friendly, we run `filestash <https://www.filestash.app/>`_. This provides a file browser web frontend to various backends, among them FTP. This is deployed with the ``file-browser`` helm chart.

==========
Deployment
==========

Deployment of Test Equipment
============================
Deployment of Test Equipment Tango Device Servers are mainly done using the ``test-equipment`` namespace.
We have two special makefile targets, ``make itf-te-template`` and ``make itf-te-install``, one for checking what will be deployed, and one for deploying the Helm charts under the ``ska-mid-itf`` umbrella.
We also have a make target that gives URLs to the deployed software: ``make itf-te-links``.

Deploying Test Equipment charts for verification
------------------------------------------------
Use the umbrella chart under `charts/test-equipment-verification` to deploy charts that were publihsed to the `Test Equipment Helm Package Registry <https://gitlab.com/ska-telescope/ska-ser-test-equipment/-/packages>`_. Note that these packages are deployed in the Helm Build job and the version number is outputted in the Job logs - example of this can be seen `here <https://gitlab.com/ska-telescope/ska-ser-test-equipment/-/jobs/4768261311>`_.

If you want to change the container image version, you can do so by editing the ``$TE_VERSION`` variable in ``/resources/makefiles/test-equipment-dev.mk``.

Sky Simulator
=============
Deployment of the Sky Simulator Control Tango Device (the RPi-hosted device that switches on and off noise sources, filters and U and V signals) follows directly (but manually) from this deployment, as the SkySimCtl Tango Device needs to be registered on the same Test Equipment namespace. This is achieved by using a triggered pipeline - see `this Confluence page <https://confluence.skatelescope.org/x/0RWKDQ>`_ for details.

Deployment of the SUT
=====================
The deployment repository for the SKA Mid Software used to be Skampi. This has now been replaced by the machinery present in this repo.
The SUT is defined in the `system-under-test` chart and can be deployed using the following jobs:

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

Currently, only 2 is fully implemented.
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

Deployment of File Browser
==========================
The spectrum analyser file browser is deployed with the ``file-browser-install`` Makefile target. It is deployed to the ``file-browser`` namespace in the ITF. The configuration file lives in the ``$FILEBROWSER_CONFIG_PATH`` environment variable on Gitlab. For local deployments, an example file is provided at ``charts/file-browser/secrets/example.json``. This doesn't provide access to the Spectrum Analyser FTP server, but does allow you to verify that the deployment is working as expected.

Namespaces and pipeline definitions
===================================
In the present repository it is possible to deploy the charts in different namespaces in the ITF cluster. In specific it is possible to deploy in the following namespaces: 

.. table:: List of namespaces at December 2023
   :widths: auto

   ================================  ====================================================
     Name                              Description
   ================================  ====================================================
   ci-ska-mid-itf-commit-ref         Used for testing purposes and normally not persisted
   ci-ska-mid-sut-skaXXX-commit-ref  Used for on demand deployment in vision of AA05 
   dish-lmc-skaXXX                   For Dish AIV related CICD jobs
   ds-sim-skaXXX                     For Dish Strcuture Simulator related CICD jobs
   file-browser                      For the spectrum analyser file browser
   integration                       For long-lived deployment of the SUT
   staging                           For long-lived deployment of the SUT
   taranta                           For taranta deployment
   test-equipment                    For Test Equipment Tango Device Servers
   ================================  ====================================================

Please note that: 

* ``commit-ref`` represents the ``CI_COMMIT_REF_NAME`` environment variables of Gitlab (the branch or tag name for which project is built),
* ``skaXXX`` represents the dish identifier (i.e. ``ska001``, ``ska002``, etc.).

For each namespace, the definition of the pipeline used for deploying the various applications is available in the folder ``.gitlab/ci/za-itf/namespace``.

For example, the definition for the namespace ``ci-ska-mid-itf-commit-ref`` is available in ``.gitlab/ci/za-itf/ci-ska-mid-itf-commit-ref/.pipeline.yaml``. It is important to note that every ``.pipeline.yaml`` definition contains an hidden gitlab job as first item in order to highlight the environment variables (parameters) set for it. 

