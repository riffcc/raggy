#!/bin/bash

# Ensure script fails on any error
set -e

# Run pytest with detailed output and coverage
pytest -v --cov=raggy --cov-report=term-missing 2>&1 | plandex tell
