#!/usr/bin/env bash
set -euo pipefail

chart_dir="$1"          # e.g. charts/ska-mid
overridden_file="$2"    # e.g. build/expected-images.txt
default_images_file="default-images.txt"

echo "Rendering default images from $chart_dir ..."

# Clean file before writing
: > "$default_images_file"

echo "Rendering default images from $chart_dir ..."

# Render top-level chart without any values
tmp_output=$(mktemp)
chart_name="$(basename "$chart_dir")"

if ! helm template "$chart_name" "$chart_dir" --values /dev/null > "$tmp_output" 2>/dev/null; then
  echo "[ERROR] Failed to render chart from $chart_dir"
  exit 1
fi

# Extract container image definitions from default render
tmp_filtered=$(mktemp)
if ! yq -o=json e '.. | select(has("containers")) | .containers[] | select(has("name") and has("image")) | .name + ":" + .image' "$tmp_output" > "$tmp_filtered" 2>/dev/null; then
  echo "[ERROR] yq failed to extract containers"
  rm -f "$tmp_output" "$tmp_filtered"
  exit 1
fi

# Clean quotes and write to final list
sed 's/^"//;s/"$//' "$tmp_filtered" >> "$default_images_file"

rm -f "$tmp_output" "$tmp_filtered"

# Sort and dedupe
sort -u "$default_images_file" -o "$default_images_file"
sort -u "$overridden_file" -o "$overridden_file"

echo "Comparing values-rendered vs default chart images..."
echo "Default images rendered from chart:"
cat "$default_images_file"

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
