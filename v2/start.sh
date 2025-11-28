#!/usr/bin/env bash
#
# start.sh - Convenience script to run the Course Planner on Unix-like systems
#
# This script simply invokes Python to run ``install_and_run.py`` in the
# current directory.  It can be double-clicked from graphical file
# managers on many Linux distributions or executed in a terminal.  If
# Python is not installed or is not accessible via ``python3``, you may
# need to adjust the shebang line or your PATH accordingly.

set -e

# Determine the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Use python3 if available, otherwise fall back to python
PY_CMD="python3"
command -v $PY_CMD >/dev/null 2>&1 || PY_CMD="python"

exec "$PY_CMD" install_and_run.py