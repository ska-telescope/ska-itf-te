================================================
Some notes on integration testing in the Mid ITF
================================================

As highlighted before, different types of tests are executed in the ITF, depending on the use-cases. The Software-only ``k8s-test-runner`` jobs may either execute in the "STFC cloud" (Techops cluster) or the Mid ITF cluster. The namespaces created for these tests have the ``ci-*`` naming convention, and are destroyed when the tests are successful. Test results are uploaded to Test Execution JIRA tickets that are created in the AT project.

Software-only environments can be targeted using Jupyter Notebooks as well, but this is rarely done.

When hardware is also included in the tests, Notebooks are used in most cases. The Jupyter Notebooks are version controlled in a sub-project of the Mid ITF, hosted at https://gitlab.com/ska-telescope/ska-mid-jupyter-notebooks. These Notebooks are used in both the Mid PSI hosted at MDA and the Mid ITF, and intimate knowledge of the environments is sometimes required to ensure configuration is correctly done.

Automated tests with hardware in-the-loop are also executed in the Mid ITF pipelines, and typically target the ``staging`` namespace. Test data is the same for both these and the software-only automated tests.

===================================
The seven commands of the telescope
===================================
Below are short sections, that could be empty, which contain the seven commands used for running observations using the TMC in automated pipeline tests.

On()
====

AssignResources()
=================
NOTE: use the handy tool provided in the Jupyter Notebooks subproject, to calculate the ``channel_count`` for an observation, as follows:

.. code-block:: python
    :linenos:
    :caption: tests/integration/resources/data/tmc/assign_resources.json

    import notebook_tools.generate_fsp as generate_fsp
    start_freq = 350000000  # Start frequency in Hz - tune to suit use case
    num_fsps_available = 4 # this is a tuneable parameter based on what is available in the setup
    end_freq = generate_fsp.calculate_end_freq(start_freq, num_fsps_available)
    print(f"Channel Count: {generate_fsp.calculate_channel_count(start_freq, end_freq)}") 



Configure()
===========
NOTE: use the handy tool provided in the Jupyter Notebooks subproject, to calculate the maximum end frequency based on number of FSPs and start frequency (same as above):

.. code-block:: python
    :linenos:
    :caption: tests/integration/resources/data/tmc/assign_resources.json

    import notebook_tools.generate_fsp as generate_fsp

    start_freq = 350000000  # Start frequency in Hz - tune to suit use case
    num_fsps_available = 4 # this is a tuneable parameter based on what is available in the setup
    print(
        f"Maximum end frequency based on params above: {generate_fsp.calculate_end_freq(start_freq, num_fsps_available)}"
    )
    print("NOTE: MAX FREQ LIMIT for BAND 1/2 is 1760000000")


Scan()
======

EndScan()
=========

End()
=====

ReleaseAllResources()
=====================

================
Testing tools
================

ska-mid-testing chart (WIP)
===========================

The `ska-mid-testing` Helm chart (Work In Progress) provides resources and utilities 
for executing integration and system tests in the Mid-AA environment. It includes a 
configurable test job for executing smoke and end-to-end tests as well as supporting 
resources to facilitate automated and manual testing and reporting workflows.

Key features
------------

- Test job which executes the *test_e2e_via_tmc* end-to-end test in main container, 
  and smoke tests from the tests/smoke in init container.
- Provides configurability for targeting different namespaces and environments using 
  environment variables set in values.yaml.
- Supports both software-only and hardware-in-the-loop testing scenarios.
- Includes test reporting and report storage and retrieval capabilities.

Executing tests in KAPB using the ska-mid-testing chart resources
-----------------------------------------------------------------
Run the following from the root of the ska-mid repository after connecting to 
the appropriate VPN:

.. code-block:: bash

   make test-e2e-kapb

The default dish IDs are set in the values file, however they can also be configured
at run time by overriding the DISH_IDS variable with the space separated dish IDs needed:

.. code-block:: bash

  # Override DISH_IDS
  make test-e2e-kapb DISH_IDS="SKA001 SKA100"

Observing smoke and end-to-end test results
-------------------------------------------
1. Shell into the `test-reports-reader` pod in the `integration-tests` namespace 
   in the za-aa-k8s-master01-k8s cluster:
   .. code-block:: bash

      kubectl exec -it -n integration-tests test-reports-reader -- /bin/bash

2. Navigate to the `/data/test-reports` directory where the reports can be found 
   in timestamped folders.

================
Smoke test suite
================

The smoke test suite is a collection of basic tests designed to verify the 
basic health of the deployed system. A high level overview of the tests in 
the suite is provided below.

CBF firmware compatibility test overview (test_qspi_bitstream_compatibility)
============================================================================
The CBF firmware compatibility test is designed to verify that the deployed 
CBF TDC MCS software is compatible with the CBF firmware loaded on the CBF 
talon boards. This test checks compatibility in two ways: version compatibility 
and bitstream checksum compatibility. Version compatibility test checks that the 
firmware version reported at active slot on the talon board has the same 
Major.Minor version of the fpga_bitstream version reported in talondx_boardmap.json 
of the deployed CBF engineering console. Bitstream checksum compatibility test 
checks that the MD5 checksum of the processing bitstream raw programming data (RPD) 
file in the engineering console PVC matches the checksum (hash) reported by the 
talon board for the active slot.

The following environment variables are used to configure the test:

- CBF_EC_MOUNT_PATH: Directory where the CBF engineering console PVC is mounted.