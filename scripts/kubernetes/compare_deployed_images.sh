#!/usr/bin/env bash
set -euo pipefail

expected_file="$1"
deployed_file="$2"

declare -A expected_versions

# Build map of expected images
while IFS=":" read -r _ image; do
  name=$(basename "$image" | cut -d':' -f1)
  expected_versions["$name"]="$image"
done < "$expected_file"

# Compare deployed images
while IFS=":" read -r name deployed_image; do
  expected_image="${expected_versions[$name]:-}"

  if [[ -z "$expected_image" ]]; then
    echo "[WARN] $name is deployed with $deployed_image, but no expected image defined"
    continue
  fi

  if [[ "$expected_image" != "$deployed_image" ]]; then
    echo "[WARN] Mismatch in '$name': expected '$expected_image', found '$deployed_image'"
  else
    echo "[INFO] $name matches expected image version"
  fi
done < "$deployed_file"
