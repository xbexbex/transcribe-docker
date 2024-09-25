#!/bin/bash

# Folder to process
FOLDER_PATH="$1"

# Loop through each file in the folder
for FILE in "$FOLDER_PATH"/*; do
    # Skip directories
    if [ -d "$FILE" ]; then
        continue
    fi
    
    # Get the modification date in the desired format (YYYY-MM-DD_HH-MM-SS)
    MOD_DATE=$(stat -c %y "$FILE" | sed 's/\..*//' | sed 's/[-:]/-/g' | sed 's/ /_/')
    
    # Extract file extension
    EXT="${FILE##*.}"
    
    # Extract the file path without extension
    FILE_NO_EXT="${FILE%.*}"
    
    # Rename the file with the new format while keeping the extension
    mv "$FILE" "${FOLDER_PATH}/${MOD_DATE}.${EXT}"
done

echo "Files renamed successfully!"
