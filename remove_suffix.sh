#!/bin/bash

# Check if the path is provided
if [ -z "$1" ]; then
    echo "Usage: $0 /path/to/directory"
    exit 1
fi

# Directory containing the files
directory="$1"

# Check if the directory exists
if [ ! -d "$directory" ]; then
    echo "Directory '$directory' does not exist."
    exit 1
fi

# Reference date in YYYY-MM-DD format
reference_date="2024-09-25"

# Convert the reference date to seconds since epoch
reference_seconds=$(date -d "$reference_date" +%s 2>/dev/null)
if [ -z "$reference_seconds" ]; then
    echo "Error: Invalid reference date format."
    exit 1
fi

# Find and process the files
find "$directory" -type f -name '* (transcribed).m4a' -print0 | while IFS= read -r -d '' file; do
    # Extract the filename
    filename=$(basename "$file")
    
    # Use regex to match the date in the filename
    if [[ "$filename" =~ ^([0-9]{4}-[0-9]{2}-[0-9]{2})_[0-9]{2}-[0-9]{2}-[0-9]{2}\ \(transcribed\)\.m4a$ ]]; then
        date_part="${BASH_REMATCH[1]}"
        
        # Convert the date from the filename to seconds since epoch
        file_seconds=$(date -d "$date_part" +%s 2>/dev/null)
        if [ -z "$file_seconds" ]; then
            echo "Skipping '$filename': Invalid date format in filename."
            continue
        fi
        
        # Compare dates
        if [ "$file_seconds" -gt "$reference_seconds" ]; then
            # Remove " (transcribed)" from the filename
            new_filename="${filename/ (transcribed)/}"
            
            # Rename the file
            mv "$file" "$directory/$new_filename"
            echo "Renamed '$filename' to '$new_filename'"
        else
            echo "Skipping '$filename': File date is before the reference date."
        fi
    else
        echo "Skipping '$filename': Filename does not match the expected pattern."
    fi
done
