#!/bin/bash
# Creates a single text file with paths and printable contents for analysis, excluding only specified unwanted files

output_file="project_content.txt"
echo "Generating $output_file with file paths and contents..."

# Clear previous output file if it exists
> "$output_file"

# Set Rust exclusions based on the flag
if [[ "$1" == "rust" ]]; then
  rust_exclusions=()   # Includes .rs files if "rust" flag is set
else
  rust_exclusions=(-path "./raggy-rs/*" -o -name "*.rs")  # Excludes Rust files otherwise
fi

# Find files, exclude unwanted patterns, and append paths and filtered contents
find . -type f \
  ! -path "./__pycache__/*" ! -name "*.pyc" \
  ! -path "./LICENSE" \
  ! -path "./.aider.*" \
  ! -path "./aider_*" ! -path "./target/*" ! -path "./.pytest_cache/*" \
  ! -path "./.git/*" ! -path "./.coverage" ! -path "./$output_file" \
  ! -name "*.db" ! -name "*.lock" ! -name ".aider.chat.history.md" \
  ! \( "${rust_exclusions[@]}" -o -name "*.rlib" -o -name "*.a" -o -name "*.so" -o -name "*.o" \) | while read -r file; do
    echo "==> $file" >> "$output_file"                 # Write file path as a header
    cat "$file" | tr -cd '\11\12\15\40-\176' >> "$output_file" # Filter printable ASCII characters
    echo -e "\n\n" >> "$output_file"                   # Add spacing between files
done

echo "Done! Contents saved in $output_file."
