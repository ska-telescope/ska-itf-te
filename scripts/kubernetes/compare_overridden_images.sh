#!/usr/bin/env bash
set -euo pipefail

chart_dir="$1"          # e.g. charts/ska-mid-itf-sut
overridden_file="$2"    # e.g. build/expected-images.txt
default_images_file="default-images.txt"

echo "Rendering default images from $chart_dir ..."

# Clean file before writing
: > "$default_images_file"

# Recursively find subcharts (directories with Chart.yaml)
find "$chart_dir" -name 'Chart.yaml' -exec dirname {} \; | while read subchart; do
  echo "Found $subchart"

  # Step 1: Helm template into a temp file
  tmp_output=$(mktemp)
  chart_name="$(basename "$subchart")"

  if ! helm template "$chart_name" "$subchart" --values /dev/null > "$tmp_output" 2>/dev/null; then
    echo "[WARN] Failed to render $subchart — skipping."
    rm -f "$tmp_output"
    continue
  fi

  # Step 2: Use yq to extract valid container image lines
  tmp_filtered=$(mktemp)
  if ! yq -o=json e '.. | select(has("containers")) | .containers[] | select(has("name") and has("image")) | .name + ":" + .image' "$tmp_output" > "$tmp_filtered" 2>/dev/null; then
    echo "[WARN] yq failed to parse output from $subchart — skipping."
    rm -f "$tmp_output" "$tmp_filtered"
    continue
  fi

  # Step 3: Strip quotes and append to master list
  sed 's/^"//;s/"$//' "$tmp_filtered" >> "$default_images_file"

  rm -f "$tmp_output" "$tmp_filtered"
done

# Sort and dedupe
sort -u "$default_images_file" -o "$default_images_file"
sort -u "$overridden_file" -o "$overridden_file"

echo "Comparing values-rendered vs default chart images..."

declare -A default_images

# Load default images
while IFS=":" read -r name image || [[ -n "$name" ]]; do
  default_images["$name"]="$image"
done < "$default_images_file"

# Compare overridden to default
while IFS=":" read -r name image || [[ -n "$name" ]]; do
  default="${default_images[$name]:-}"
  if [[ -n "$default" && "$default" != "$image" ]]; then
    echo "[OVERRIDE] $name image overridden: default='$default' vs values='$image'"
  fi
done < "$overridden_file"

# Detect new containers introduced by values
while IFS=":" read -r name image || [[ -n "$name" ]]; do
  if [[ -z "${default_images[$name]:-}" ]]; then
    echo "[OVERRIDE] $name is introduced only via values: '$image'"
  fi
done < "$overridden_file"
