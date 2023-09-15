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
There are various integration points for the DishLMC integration activities in the Mid ITF.

DishLMC <> Dish Structure integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
An OPC UA server is deployed in the K8s Cluster in the Mid ITF. Any instance of the DishLMC can be connected to an instance of the DishStructure Simulator. Details for connecting to the DS Simulator(s) are available in `Confluence <https://confluence.skatelescope.org/x/Jz6KDQ>`_. For assistance, please reach out in `#team-itf-support <https://skao.slack.com/archives/C03PC2M2VGA>`_. A dedicated channel also exists for discussing issues around the Dish Structure Simulator: `#temp-dish-structure-simulator-itf <https://skao.slack.com/archives/C05CJMS3W20>`_.

DishLMC <> SPFRx integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For integration with the SPFRx, there are two SPFRx hardware devices available at the Mid ITF. Integration activities with the hardware is under control and management of the Dish AIV group and led by the KAROO and CIPA teams.
A dedicated Slack channel exists for discussing issues around integration with the SPFRx: `#mid-itf-dishlmc-spfrx-integration <https://skao.slack.com/archives/C05QYPKLJNS>`_. There is also a channel that was established for discussing the installation of the SPFRx in the Mid ITF: `#temp-spfrx-installation-at-itf <https://skao.slack.com/archives/C054R2Q1UGH>`_.

DishLMC <> TMC Software integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For testing integration of the TMC with the DishLMC, our initial setup includes a choice of a single- or multiple-instance deployment of DishLMC. The multiple-instance deployment contains four dishes, being the four intended DishIDs for AA0.5. All instances are deployed with Simulators activated for the subservient devices. For more information, consult the `README of the DishLMC project <https://gitlab.com/ska-telescope/ska-dish-lmc>`_, and also the documentation for the subservient devices.
In order to deploy all four instances of DishLMC, one needs to trigger the CI pipeline job in the SUT stage `as well as` the first dish (SKA001) in the Dish AIV stage. Refer to the list of `pipeline jobs running from the main branch <https://gitlab.com/ska-telescope/ska-mid-itf/-/pipelines?page=1&scope=all&ref=main>`_ - try to use the latest pipeline to deploy from main.
 If you need only one dish, only deploy it from the DishAIV stage.


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
The deployment repository for the SKA Mid Software used to be Skampi. There is currently uncertainty about the continued usage of Skampi for deploying software at the Mid ITF or on site.


Deployment of File Browser
==========================
The spectrum analyser file browser is deployed with the ``file-browser-install`` Makefile target. It is deployed to the ``file-browser`` namespace in the ITF. The configuration file lives in the ``$FILEBROWSER_CONFIG_PATH`` environment variable on Gitlab. For local deployments, an example file is provided at ``charts/file-browser/secrets/example.json``. This doesn't provide access to the Spectrum Analyser FTP server, but does allow you to verify that the deployment is working as expected.