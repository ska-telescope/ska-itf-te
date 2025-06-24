#!/bin/bash
# Usage: update_testing_image_tag.sh X.X.X path/to/values.yaml

TAG="$1"
FILE="$2"

yq -i ".image.tag = \"${TAG}\"" "$FILE"
