#!/usr/bin/env bash
# Extracts the ska-mid chart version from charts/ska-mid/Chart.yaml in the
# current workspace and prints it to stdout.
#
# Usage: bash .gitlab/ci/za-itf/upgrading/get_chart_version.sh
set -euo pipefail

CHART_FILE="charts/ska-mid/Chart.yaml"

if [ ! -f "${CHART_FILE}" ]; then
    echo "ERROR: ${CHART_FILE} not found" >&2
    exit 1
fi

VERSION=$(grep '^version:' "${CHART_FILE}" | sed 's/^version: *//;s/"//g;s/ //g')

if [ -z "${VERSION}" ]; then
    echo "ERROR: Could not extract version from ${CHART_FILE}" >&2
    exit 1
fi

echo "${VERSION}"
