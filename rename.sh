#!/bin/bash

# Directory containing the files
directory="/mnt/share/recordings/transcriptions"

find "$directory" -type f -name 'r___*-*-*_*_*.*' | while read -r file; do
    echo "Processing file: $file"
    
    # Extract the basename
    base_name=$(basename "$file")
    echo "Base name: $base_name"
    
    # Separate extension and filename
    extension="${base_name##*.}"
    file_name="${base_name%.*}"
    echo "Filename without extension: $file_name"
    echo "Extension: $extension"
    
    # Remove the 'r___' prefix
    file_name_no_prefix="${file_name#r___}"
    echo "Filename without prefix: $file_name_no_prefix"
    
    # Extract date, time, and duration parts
    IFS='_' read -r date_part time_part duration_part <<< "$file_name_no_prefix"
    echo "Date part: $date_part"
    echo "Time part: $time_part"
    echo "Duration part: $duration_part"
    
    # Check that all parts are present
    if [[ -z "$date_part" || -z "$time_part" || -z "$duration_part" ]]; then
        echo "Skipping file with unexpected format: $base_name"
        continue
    fi

    # Reformat date and time
    IFS='-' read -r year month day <<< "$date_part"
    IFS='-' read -r hour minute second <<< "$time_part"

    # Check that date and time parts are present
    if [[ -z "$year" || -z "$month" || -z "$day" || -z "$hour" || -z "$minute" || -z "$second" ]]; then
        echo "Skipping file with invalid date/time: $base_name"
        continue
    fi

    echo "Year: $year, Month: $month, Day: $day"
    echo "Hour: $hour, Minute: $minute, Second: $second"

    # Replace underscores with spaces in duration_part
    duration_part="${duration_part//_/ }"

    # Format new filename and include the extension
    new_file_name="r___${year}___${month}___${day}  ${hour}.${minute}.${second}  (${duration_part}).${extension}"

    # Rename the file
    mv "$file" "$directory/$new_file_name"

    echo "Renamed: $file -> $new_file_name"
done
