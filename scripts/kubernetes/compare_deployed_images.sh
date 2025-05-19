#!/usr/bin/env bash
set -euo pipefail

expected_file="$1"
deployed_file="$2"

declare -A expected_versions
declare -A deployed_versions

# Load expected
while IFS=":" read -r name image_tag || [[ -n "$name" ]]; do
  name="${name//\"/}"; name="${name## }"; name="${name%% }"
  image_tag="${image_tag//\"/}"; image_tag="${image_tag## }"; image_tag="${image_tag%% }"
  [[ -n "$name" && -n "$image_tag" ]] && expected_versions["$name"]="$image_tag"
done < "$expected_file"

# Load deployed
while IFS=":" read -r name image_tag || [[ -n "$name" ]]; do
  name="${name//\"/}"; name="${name## }"; name="${name%% }"
  image_tag="${image_tag//\"/}"; image_tag="${image_tag## }"; image_tag="${image_tag%% }"
  [[ -n "$name" && -n "$image_tag" ]] && deployed_versions["$name"]="$image_tag"
done < "$deployed_file"

echo "[DEBUG] Checking deployed vs expected container versions..."

# Check all expected containers
for name in "${!expected_versions[@]}"; do
  expected_image="${expected_versions[$name]}"
  deployed_image="${deployed_versions[$name]:-}"

  if [[ -z "$deployed_image" ]]; then
    echo "[DEBUG] $name is expected with $expected_image, but not deployed"
    continue
  fi

  if [[ "$expected_image" != "$deployed_image" ]]; then
    echo "[WARN] Mismatch in '$name': expected '$expected_image', found '$deployed_image'"
  else
    echo "[INFO] $name matches expected image version"
  fi
done

# Check if there are extra deployed containers not in expected
for name in "${!deployed_versions[@]}"; do
  if [[ -z "${expected_versions[$name]:-}" ]]; then
    echo "[DEBUG] $name is deployed with ${deployed_versions[$name]}, but no expected image defined"
  fi
done
