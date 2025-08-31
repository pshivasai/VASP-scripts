import os
import re

def find_outcar_in_molecule_dir(molecule_dir):
    """
    Searches for the OUTCAR file within a specific molecule directory.
    
    The search follows this logic:
    1. Look in molecule_dir -> sp/
    2. If not found, look in molecule_dir -> restart/ -> sp/
    
    Args:
        molecule_dir (str): The path to the specific molecule's directory.
        
    Returns:
        str: The full path to the OUTCAR file, or None if not found.
    """
    # Case 1: Look for the 'sp' directory directly inside the molecule directory
    sp_dir = os.path.join(molecule_dir, 'sp')
    if os.path.isdir(sp_dir):
        outcar_path = os.path.join(sp_dir, 'OUTCAR')
        if os.path.isfile(outcar_path):
            print(f"Found OUTCAR at: {outcar_path}")
            return outcar_path
    
    # Case 2: If 'sp' is not found, look inside a 'restart' directory
    restart_dir = os.path.join(molecule_dir, 'restart')
    if os.path.isdir(restart_dir):
        sp_dir_in_restart = os.path.join(restart_dir, 'sp')
        if os.path.isdir(sp_dir_in_restart):
            outcar_path = os.path.join(sp_dir_in_restart, 'OUTCAR')
            if os.path.isfile(outcar_path):
                print(f"Found OUTCAR at: {outcar_path}")
                return outcar_path
                
    return None

def parse_outcar(outcar_path, outfile):
    """
    Parses the OUTCAR file to extract VBM and CBM values for each k-point,
    finds the minimum band gap, and writes the results to a file.
    
    Args:
        outcar_path (str): The full path to the OUTCAR file.
        outfile (file object): The file to write the results to.
    """
    print("--- Parsing OUTCAR and writing results to file ---")
    try:
        with open(outcar_path, 'r') as f:
            lines = f.readlines()

        kpoint_data = {}
        current_kpoint = None
        
        # Regex to find the start of a k-point block
        kpoint_regex = re.compile(r"^\s*k-point\s+(\d+)\s*:.*")
        # Regex to find band energy lines (e.g., "  248   -1.3644   2.00000")
        band_regex = re.compile(r"^\s*\d+\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$")

        for line in lines:
            kpoint_match = kpoint_regex.match(line)
            if kpoint_match:
                current_kpoint = int(kpoint_match.group(1))
                kpoint_data[current_kpoint] = {'vbm': None, 'cbm': None}
                continue

            if current_kpoint is not None:
                band_match = band_regex.match(line)
                if band_match:
                    energy = float(band_match.group(1))
                    occupation = float(band_match.group(2))

                    # VBM is the highest energy level with an occupation > 0
                    if occupation > 0.0:
                        kpoint_data[current_kpoint]['vbm'] = energy
                    
                    # CBM is the first energy level with an occupation == 0
                    # that comes after a VBM has been found.
                    elif occupation == 0.0 and kpoint_data[current_kpoint]['vbm'] is not None and kpoint_data[current_kpoint]['cbm'] is None:
                        kpoint_data[current_kpoint]['cbm'] = energy

        # --- Write the detailed results to the file ---
        if not kpoint_data:
            outfile.write("No k-point data was extracted. Check the OUTCAR file format.\n")
            return

        outfile.write("\nResults (All K-Points):\n")
        outfile.write("-" * 40 + "\n")
        min_band_gap = float('inf')
        min_gap_data = None

        for kpoint, values in sorted(kpoint_data.items()):
            vbm = values['vbm']
            cbm = values['cbm']
            
            if vbm is not None and cbm is not None:
                band_gap = cbm - vbm
                outfile.write(f"K-Point: {kpoint}\n")
                outfile.write(f"  VBM: {vbm:.4f} eV\n")
                outfile.write(f"  CBM: {cbm:.4f} eV\n")
                outfile.write(f"  Band Gap: {band_gap:.4f} eV\n")
                outfile.write("-" * 40 + "\n")
                
                # Check if this is the new minimum band gap
                if band_gap < min_band_gap:
                    min_band_gap = band_gap
                    min_gap_data = {
                        'kpoint': kpoint,
                        'vbm': vbm,
                        'cbm': cbm,
                        'gap': band_gap
                    }
            else:
                outfile.write(f"K-Point: {kpoint} - Incomplete data (VBM or CBM not found).\n")
                outfile.write("-" * 40 + "\n")

        # --- Write the summary section for the minimum band gap ---
        outfile.write("\n--- Summary ---\n")
        if min_gap_data:
            outfile.write(f"Minimum Band Gap found at K-Point: {min_gap_data['kpoint']}\n")
            outfile.write(f"  VBM: {min_gap_data['vbm']:.4f} eV\n")
            outfile.write(f"  CBM: {min_gap_data['cbm']:.4f} eV\n")
            outfile.write(f"  Band Gap: {min_gap_data['gap']:.4f} eV\n")
        else:
            outfile.write("No valid band gap could be calculated from the data.\n")
        outfile.write("-" * 40 + "\n")


    except FileNotFoundError:
        error_msg = f"Error: The file at {outcar_path} was not found.\n"
        print(error_msg.strip())
        outfile.write(error_msg)
    except Exception as e:
        error_msg = f"An unexpected error occurred: {e}\n"
        print(error_msg.strip())
        outfile.write(error_msg)


if __name__ == "__main__":
    start_directory = os.getcwd()
    output_filename = "vbm_cbm_results.txt"
    
    print(f"Starting search in: {start_directory}")
    print(f"Results will be saved to: {output_filename}")

    # Open the output file to write all results
    with open(output_filename, 'w') as outfile:
        found_any_outcar = False
        for item in os.listdir(start_directory):
            potential_molecule_dir = os.path.join(start_directory, item)
            
            # Check if the item is a directory
            if os.path.isdir(potential_molecule_dir):
                print(f"\n==================================================")
                print(f"Processing Molecule Directory: {item}")
                print(f"==================================================")
                
                # Write a header for this molecule in the output file
                outfile.write(f"\n==================================================\n")
                outfile.write(f"Results for Molecule Directory: {item}\n")
                outfile.write(f"==================================================\n")
                
                outcar_file = find_outcar_in_molecule_dir(potential_molecule_dir)
                
                if outcar_file:
                    found_any_outcar = True
                    # Pass the file object to the parsing function
                    parse_outcar(outcar_file, outfile)
                else:
                    message = f"--> No 'sp' directory with an OUTCAR file found in '{item}'.\n"
                    print(message.strip())
                    outfile.write(message)

    if not found_any_outcar:
        print("\nExecution finished. No OUTCAR files were found in any of the subdirectories.")
    else:
        print(f"\nExecution finished. All results have been saved to '{output_filename}'.")
