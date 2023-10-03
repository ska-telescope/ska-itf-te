#!/bin/bash
# Usage: bash resources/gitlab_section.sh <label> "<Command Description>" <command>
# Example: bash resources/gitlab_section.sh current_time "Show the current time" date
#
# This differs from the script in .make in that it will exit with a non-zero exit code
# if what is being executed fails or if there are unset variables.

set -eu
set -o pipefail

echo -e "section_start:`date +%s`:$1[collapsed=true]\r\e[0K$2"
${@:3}
echo -e "section_end:`date +%s`:$1\r\e[0K"
