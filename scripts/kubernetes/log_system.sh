#!/bin/bash

set -eu
set -o pipefail

# Finds all pods associated with a specified system and downloads their logs.
# The pods and the downloaded logs' location are displayed.
#
# Parameters (REQUIRED):
#   1: the Kubernetes system used to find the pods. e.g. sdp
#   2: the Kubernetes namespace within which to look for the pods.
#
# Example usage: Find all logs for SDP in the integration namespace:
# $ scripts/kubernetes/log_system.sh sdp integration

system=${1}
namespace=${2}

script_dir=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
source ${script_dir}/log_by_selector.sh

export selector="system=${system}"
export namespace=${namespace}
echo "Collecting logs for ${system} in ${namespace}"
log_by_selector
