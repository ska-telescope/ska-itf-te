# Mid ITF Configuration and Test Results

The `upload_to_confluence` script updates an existing confluence page with the results of Integration Tests and configuration of the System Under Test at MID ITF.
The `generate_diagrams` script is used to generate only the diagrams from System Under Test configuration locally.

## Install

Install the `ska-ser-skallop` Python package.

```bash
pip3 install -U ska-ser-skallop --extra-index-url https://artefact.skao.int/repository/pypi-internal/simple
```

Once installed the `upload-to-confluence` and `generate-sut-diagrams` scripts will be available in your Python bin directory.

Alternatively, the scripts can also be installed with `poetry install` from this repository.

## Usage

### upload-to-confluence

```bash
usage: upload-to-confluence [configfile] [resultsfile]

Retrieve a feature file from an XTP ticket. Your JIRA username and password will be required to perform this operation

optional arguments:

   --help show this help message and exit

   --configfile path to SUT configuration file

   --resultsfile Test results
```

### generate-sut-diagrams

```bash
usage: generate-sut-diagrams [-h] configfile

Generate diagrams from system dependency configuration file.

positional arguments:
  configfile  The configuration file representing the system

options:
  -h, --help  show this help message and exit
```
