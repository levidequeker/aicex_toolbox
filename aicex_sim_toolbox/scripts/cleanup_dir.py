# PURPOSE: Cleaning up an output_tran directory full of files such as 'tran_SchGtKttTtVt_VDD100.spi', f.e. after a faulty simulation run.

# BENEFIT: Life's too short for rm'ing all files.

# HOW: With some RegEx extravaganza.

# USER INSTRUCTIONS: Fill in the path to the directory, the regex pattern and indicate if you want to do a dry run or actually delete files (configs under main below). Lean back and enjoy your gained time.

import os
import re
from pathlib import Path

def check_file(file_path: Path, pattern: str) -> bool:
    """
    Returns True if file matches the naming convention.
    Pattern is a regular expression.
    """
    return re.match(pattern, file_path.name) is not None

def delete_files(directory: Path, pattern: str, dry_run: bool = True):
    """
    Deletes files in 'directory' that match 'pattern'.

    Parameters:
        directory (Path): Target directory
        pattern (str): Regex pattern for filenames
        dry_run (bool): If True, only prints what would be deleted
    """
    if not directory.exists() or not directory.is_dir():
        raise ValueError(f"{directory} is not a valid directory.")

    for file_path in directory.iterdir():
        if file_path.is_file() and check_file(file_path, pattern):
            if dry_run:
                print(f"[DRY RUN] Would delete: {file_path}")
            else:
                print(f"Deleting: {file_path}")
                file_path.unlink()

def main():
    ### USER CONFIG ###
    #path_to_dir = Path("/path/to/your/directory") # Use this if the scrip is NOT in the target directory
    path_to_dir = Path(os.getcwd()) # Use this if you execute the python script in your desired folder
    pattern = r"tran_SchGtKttTtVt_.*" # Name pattern of the series of files you want to delete
    ### END USER CONFIG ###

    delete_files(path_to_dir, pattern, dry_run=True)
    delete_confirmation = input("\nProceed with deletion? [y/N]: ").strip().lower()
    if delete_confirmation == 'y':
        print("Deleting...")
        delete_files(path_to_dir, pattern, dry_run=False)
    else:
        print("Deleting aborted!")

if __name__ == "__main__":
    main()

