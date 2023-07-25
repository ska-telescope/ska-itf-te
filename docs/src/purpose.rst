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
We use an OPC UA server in the K8s Cluster in the Mid ITF to simulate the Dish Structure (DS)for DishLMC integration. Details for connecting to the DS Simulator are available in `Confluence <https://confluence.skatelescope.org/x/Jz6KDQ>`_. For assistance, please reach out in `#team-itf-support <https://skao.slack.com/archives/C03PC2M2VGA>`.

==========
Deployment
==========

Deployment of Test Equipment
============================
Deployment of Test Equipment Tango Device Servers are mainly done using the `test-equipment` namespace.
We have two special makefile targets, `make itf-te-template` and `make itf-te-install`, one for checking what will be deployed, and one for deploying the Helm charts under the `ska-mid-itf` umbrella.
We also have a make target that gives URLs to the deployed software: `make itf-te-links`.

Sky Simulator
=============
Deployment of the Sky Simulator Control Tango Device (the RPi-hosted device that switches on and off noise sources, filters and U and V signals) follows directly (but manually) from this deployment, as the SkySimCtl Tango Device needs to be registered on the same Test Equipment namespace. This is achieved by using a triggered pipeline - see `this Confluence page <https://confluence.skatelescope.org/x/0RWKDQ>`_ for details.

Deployment of the SUT
=====================
The deployment repository for the SKA Mid Software used to be Skampi. There is currently uncertainty about the continued usage of Skampi for deploying software at the Mid ITF or on site.

