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

    ~~~~~~~
    import notebook_tools.generate_fsp as generate_fsp
    start_freq = 350000000  # Start frequency in Hz - tune to suit use case
    num_fsps_available = 4 # this is a tuneable parameter based on what is available in the setup
    end_freq = generate_fsp.calculate_end_freq(start_freq, num_fsps_available)
    print(f"Channel Count: {generate_fsp.calculate_channel_count(start_freq, end_freq)}") 
    ~~~~~~~



Configure()
===========
NOTE: use the handy tool provided in the Jupyter Notebooks subproject, to calculate the maximum end frequency based on number of FSPs and start frequency (same as above):

.. code-block:: python
    :linenos:
    :caption: tests/integration/resources/data/tmc/assign_resources.json

    ~~~~~~~
    import notebook_tools.generate_fsp as generate_fsp

    start_freq = 350000000  # Start frequency in Hz - tune to suit use case
    num_fsps_available = 4 # this is a tuneable parameter based on what is available in the setup
    print(
        f"Maximum end frequency based on params above: {generate_fsp.calculate_end_freq(start_freq, num_fsps_available)}"
    )
    print("NOTE: MAX FREQ LIMIT for BAND 1/2 is 1760000000")
    ~~~~~~~


Scan()
======

EndScan()
=========

End()
=====

ReleaseAllResources()
=====================


