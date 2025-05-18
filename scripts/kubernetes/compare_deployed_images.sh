#!/usr/bin/env bash
set -euo pipefail

expected_file="$1"
deployed_file="$2"

declare -A expected_versions

# Build map of expected images
while IFS=":" read -r name image; do
  # Sanitise both name and image
  name="${name//\"/}"   # remove quotes
  name="${name## }"     # trim leading space
  name="${name%% }"     # trim trailing space

  image="${image//\"/}"
  image="${image## }"
  image="${image%% }"

  if [[ -n "$name" && -n "$image" ]]; then
    expected_versions["$name"]="$image"
  fi
done < "$expected_file"

echo "[DEBUG] Loaded expected images:"
for k in "${!expected_versions[@]}"; do
  echo "  $k -> ${expected_versions[$k]}"
done

# Compare deployed to expected
while IFS=":" read -r name deployed_image || [[ -n "$name" ]]; do
  name="${name//\"/}"
  name="${name## }"
  name="${name%% }"

  deployed_image="${deployed_image//\"/}"
  deployed_image="${deployed_image## }"
  deployed_image="${deployed_image%% }"

  if [[ -z "$name" || -z "$deployed_image" ]]; then
    continue
  fi

  expected_image="${expected_versions[$name]:-}"

  if [[ -z "$expected_image" ]]; then
    echo "[WARN] $name is deployed with $deployed_image, but no expected image defined"

  elif [[ "$expected_image" != "$deployed_image" ]]; then
    echo "[WARN] Mismatch in '$name': expected '$expected_image', found '$deployed_image'"

  else
    echo "[INFO] $name matches expected image version"
  fi
done < "$deployed_file"
