#!/bin/bash

# Ensure script fails on any error
set -e

# Prompt
echo 'Please solve the following issues with Pytest output' | tee test.out

# Install package in development mode
pip3 install -e . --break-system-packages

# Run pytest with detailed output and coverage
pytest -v --cov=raggy --cov-report=term-missing 2>&1 | tee test.out && plandex tell -f test.out --bg
