import os

def find_sp_directory(base_path):
    """
    Searches for a directory named 'sp' within the base_path.
    It first checks the base_path directly. If not found, it then
    checks inside a 'restart' directory.

    Args:
        base_path (str): The path to the directory to start the search from.

    Returns:
        str: The full path to the 'sp' directory if found, otherwise None.
    """
    # Case 1: Check if 'sp' is directly inside the base_path
    direct_sp_path = os.path.join(base_path, 'sp')
    if os.path.isdir(direct_sp_path):
        return direct_sp_path

    # Case 2: If not found, check inside a 'restart' directory
    restart_path = os.path.join(base_path, 'restart')
    if os.path.isdir(restart_path):
        restart_sp_path = os.path.join(restart_path, 'sp')
        if os.path.isdir(restart_sp_path):
            return restart_sp_path

    # If we've searched both places and not found it
    return None

def extract_fermi_energy(sp_path, filename="OUTCAR"):
    """
    Opens a file within the 'sp' directory, finds the line with
    'E-fermi', and extracts the corresponding value.

    Args:
        sp_path (str): The path to the 'sp' directory.
        filename (str): The name of the output file to read.
                        Defaults to "OUTCAR", a common VASP output file.

    Returns:
        float: The Fermi energy value if found, otherwise None.
    """
    file_path = os.path.join(sp_path, filename)

    if not os.path.isfile(file_path):
        print(f"Error: File '{filename}' not found in '{sp_path}'.")
        return None

    try:
        with open(file_path, 'r') as f:
            for line in f:
                # Check if the target string is in the current line
                if 'E-fermi' in line:
                    # The line looks like: " E-fermi :  -1.2406   XC(G=0): ..."
                    # We split the line by spaces to separate the words
                    parts = line.split()
                    try:
                        # Find the index of the colon ':'
                        # The value we want is right after it.
                        colon_index = parts.index(':')
                        fermi_value = float(parts[colon_index + 1])
                        return fermi_value
                    except (ValueError, IndexError):
                        # This handles cases where the line has 'E-fermi' but
                        # is formatted unexpectedly.
                        print(f"Warning: Could not parse line: {line.strip()}")
                        continue
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return None

    # If the loop finishes and 'E-fermi' was never found
    return None

def main():
    """
    Main function to run the script in a loop.
    """
    print("--- Fermi Energy Extractor ---")
    current_directory = os.getcwd()
    print(f"Running from: {current_directory}")
    print("Enter directory name or 'quit' to exit.")

    while True: # Start an infinite loop
        # Ask the user for the folder to investigate
        target_dir = input("\n> ")

        # Check if the user wants to exit the loop
        if target_dir.lower() == 'quit':
            print("Goodbye!")
            break # Exit the while loop

        # The full path to the user-specified directory
        full_target_path = os.path.join(current_directory, target_dir)

        if not os.path.isdir(full_target_path):
            print(f"Error: Directory '{target_dir}' not found.")
            continue # Skip to the next iteration of the loop

        # 1. Find the 'sp' directory
        sp_directory_path = find_sp_directory(full_target_path)

        if not sp_directory_path:
            print(f"Error: No 'sp' directory found in '{target_dir}' or '{os.path.join(target_dir, 'restart')}'.")
            continue # Skip to the next iteration

        # 2. Extract the Fermi energy from the output file
        fermi_energy = extract_fermi_energy(sp_directory_path, filename="OUTCAR")

        if fermi_energy is not None:
            # A more compact success message
            print(f"{target_dir}: {fermi_energy}")
        else:
            # A more compact failure message
            print(f"Error: Could not extract E-fermi from '{target_dir}'.")


if __name__ == "__main__":
    main()
