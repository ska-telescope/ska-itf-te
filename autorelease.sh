#!/bin/bash

# Configuration: Update these if needed
REMOTE="origin"
BRANCH=$(git rev-parse --abbrev-ref HEAD) # Current local branch
INTERVAL=60                               # Check every 60 seconds

echo "Monitoring $REMOTE/$BRANCH for changes..."

while true; do
    # 1. Update local remote-tracking branches without merging
    git fetch $REMOTE $BRANCH -q 

    # 2. Count how many commits the local branch is behind the remote
    # Syntax: HEAD..@{u} compares current branch to its upstream
    BEHIND_COUNT=$(git rev-list --count HEAD..@{u})

    if [ "$BEHIND_COUNT" -gt 0 ]; then
        echo "$(date): Found $BEHIND_COUNT new commit(s). Pulling updates..."
        continue
    fi

    sleep $INTERVAL
done

git pull --ff-only
Publish