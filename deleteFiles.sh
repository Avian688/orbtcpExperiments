#!/bin/bash

# Find all files with the specified extensions recursively
find . -type f \( -iname "*.json" -o -iname "*.xml" -o -iname "*.anf" -o -iname "*.vec" -o -iname "*.vci" -o -iname "*.sca" -o -iname "*.txt" \) -delete

# Inform the user about the action taken
echo "All files with extensions .txt, .json, .xml, .anf, .vec, .vci, and .sca have been removed."
