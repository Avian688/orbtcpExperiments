#!/bin/bash

# List of directories to build in the desired order
directories=("inet4.5" "tcpGoodputApplications" "tcpPaced" "cubic" "bbr" "orbtcp")

# Iterate through each directory
for dir in "${directories[@]}"; do
  echo "Processing directory: $dir"

  # Check if the directory exists
  if [ -d "$dir" ]; then
    # Change into the directory
    cd "$dir" || exit

    # Run the make command
    echo "Running 'make' in $dir..."
    make

    # Go back to the parent directory
    cd ..
  else
    echo "Warning: Directory $dir does not exist. Skipping."
  fi

  echo ""
done

echo "Script completed."