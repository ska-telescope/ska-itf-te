#!/usr/bin/env bash
set -euo pipefail

chart_dir="$1"
echo "Scanning chart directory for image overrides: $chart_dir"

# Find all values.yaml files in the chart directory tree
values_files=$(find "$chart_dir" -type f -name "values.yaml")

found=0

for file in $values_files; do
  echo "Checking $file"

  # Search for image overrides (tag, image, registry)
  overrides=$(yq e '.. | select(tag == "!!map") | select(has("image")) | .image | select(has("tag") or has("registry") or has("image"))' "$file")

  if [[ -n "$overrides" ]]; then
    echo "[OVERRIDES] Found explicit image overrides in: $file"
    echo "$overrides"
    echo
    found=1
  fi
done

if [[ "$found" -eq 1 ]]; then
  echo "[INFO] Explicit container image overrides detected in chart values"
else
  echo "[INFO] No image overrides found in any values.yaml"
fi
