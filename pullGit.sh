#!/bin/bash

# List of directories to pull from GitHub
directories=("bbr" "cubic" "inet4.5" "orbtcp" "tcpPaced" "tcpGoodputApplications")

# Iterate through each directory
for dir in "${directories[@]}"; do
  echo "Processing directory: $dir"
  
  # Check if the directory exists
  if [ -d "$dir" ]; then
    # Change into the directory
    cd "$dir" || exit
    
    # Forcefully sync the local repository with the remote
    echo "Fetching and resetting to the remote branch for $dir..."
    git fetch --all
    git reset --hard HEAD
    
    # Remove untracked files and directories
    echo "Cleaning untracked files for $dir..."
    git clean -fd
    
    # Go back to the parent directory
    cd ..
  else
    echo "Warning: Directory $dir does not exist. Skipping."
  fi

  echo ""
done

echo "Script completed."