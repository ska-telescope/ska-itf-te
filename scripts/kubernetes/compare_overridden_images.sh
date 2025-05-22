#!/usr/bin/env bash
set -euo pipefail

chart_dir="$1"                         # charts/ska-mid-itf-sut
overridden_file="$2"                  # build/expected-images.txt
default_images_file="default-images.txt"

echo "Rendering default images from $chart_dir ..."

# Clean file before writing
: > "$default_images_file"

# Recursively find subcharts (directories with Chart.yaml)
find "$chart_dir" -name 'Chart.yaml' -exec dirname {} \; | while read subchart; do
  echo "[DEBUG] Template default for $subchart"
  helm template "$subchart" > tmp.yaml || true
  yq e '.. | select(has("containers")) | .containers[] | .name + ":" + .image' tmp.yaml >> "$default_images_file"
done

sort -u "$default_images_file" -o "$default_images_file"
sort -u "$overridden_file" -o "$overridden_file"

echo "Comparing values-rendered vs default chart images..."

declare -A default_images

# Load default images
while IFS=":" read -r name image || [[ -n "$name" ]]; do
  default_images["$name"]="$image"
done < "$default_images_file"

# Compare to overridden images
while IFS=":" read -r name image || [[ -n "$name" ]]; do
  default="${default_images[$name]:-}"
  if [[ -n "$default" && "$default" != "$image" ]]; then
    echo "[OVERRIDE] $name image overridden: default='$default' vs values='$image'"
  fi
done < "$overridden_file"

# Detect new containers not present in defaults
while IFS=":" read -r name image || [[ -n "$name" ]]; do
  if [[ -z "${default_images[$name]:-}" ]]; then
    echo "[OVERRIDE] $name is introduced only via values: '$image'"
  fi
done < "$overridden_file"
