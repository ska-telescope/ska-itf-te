#!/bin/bash

set -eu
set -o pipefail

# Finds all pods associated with a specified subsystem and downloads their logs.
# The pods and the downloaded logs' location are displayed.
#
# Parameters (REQUIRED):
#   1: the Kubernetes subsystem used to find the pods. e.g. ska-tmc-mid
#   2: the Kubernetes namespace within which to look for the pods.
#
# Example usage: Find all logs for dish LMC in the integration namespace:
# $ scripts/kubernetes/log_subsystem.sh ska-dish-lmc integration

subsystem=${1}
namespace=${2}

script_dir=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
source ${script_dir}/log_by_selector.sh

export selector="subsystem=${subsystem}"
export namespace=${namespace}
echo "Collecting logs for ${subsystem} in ${namespace}"
log_by_selector
