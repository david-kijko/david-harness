#!/usr/bin/env bash
# Usage: recall.sh <query>
exec kijko-memory --limit 5 recall "$@"
