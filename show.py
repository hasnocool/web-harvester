import os
import sys

def display_python_files(directory, current_script, depth=0):
    """
    Recursively search for and display the contents of .py files in a directory,
    excluding the current script. Skips hidden directories and files.
    
    Args:
    - directory: The directory to search in.
    - current_script: The name of the script to exclude from the search.
    - depth: The current depth of the recursive search, used to skip the script's directory.
    """
    # Separator for readability, adjusted for depth to indicate level
    separator = "-" * (40 - depth * 2)
    
    # Avoid searching the directory of the current script at depth 0
    if depth > 0 or os.path.basename(directory) != os.path.dirname(current_script):
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            # Skip hidden files and directories
            if filename.startswith('.'):
                continue
            if os.path.isdir(filepath):
                # Recurse into subdirectories
                display_python_files(filepath, current_script, depth + 1)
            elif filename.endswith('.py') and filepath != current_script:
                # Display the .py file contents, excluding the current script
                print(separator)
                print(f"Filename: {filename} (in {directory})")
                print(separator)
                with open(filepath, 'r') as file:
                    print(file.read())
                print(separator)  # Additional separator for better readability

# Get the current script's path
current_script = os.path.abspath(sys.argv[0])

# Display .py files in the current directory
display_python_files('.', current_script)

# Additionally, display .py files in the 'modules/' directory, if it exists
modules_dir = 'modules'
if os.path.exists(modules_dir) and os.path.isdir(modules_dir):
    display_python_files(modules_dir, current_script)
