#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 VERSION FILE" >&2
    exit 2
fi

version=$1
file=$2
if [ ! -f "$file" ]; then
    echo "File not found: $file" >&2
    exit 1
fi

temporary_file=$(mktemp "${file}.tmp.XXXXXX")
trap 'rm -f "$temporary_file"' 0 HUP INT TERM

sed "s/^version: .*/version: $version/" "$file" > "$temporary_file"
cat "$temporary_file" > "$file"
