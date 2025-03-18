#!/bin/bash

# Define the directories to push
dirs=("bbr" "cubic" "inet4.5" "orbtcp" "orbtcpExperiments" "tcpGoodputApplications" "tcpPaced")

# Iterate over each directory
for dir in "${dirs[@]}"; do 
  echo "Processing directory: $dir"  # Print the directory name

  cd "$dir" || continue  # Change to the directory or skip if it doesn't exist

  # Add all changes in the current directory
  git add .

  # Commit changes with a generic message
  git commit -m "Automated commit" 

  # Attempt a normal git push
  git push origin master

  # If the push fails, attempt a force push
  if [ $? -ne 0 ]; then
    echo "Normal push failed for $dir. Attempting force push..."
    git push origin master -f
  fi

  cd ..  # Go back to the parent directory
done

echo "Finished pushing all directories."