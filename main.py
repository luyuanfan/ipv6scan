import sys
import os
import bz2
import ipaddress
from collections import Counter

FOUT = "non_slaac.csv"

def is_slaac(addr):
    full = addr.exploded.replace(":", "")
    return full[22:26].lower() == "fffe"

def process_file(filepath, fout): 
    total = 0
    slaac_count = 0

    if not filepath.endswith(".csv.bz2"):
        return 

    with bz2.open(filepath, "rt") as f:
        for line in f:
            line = line.strip()
            # skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            columns = line.split(",")
            if len(columns) < 3:
                continue

            # get SrcIP in column 3
            src_ip_str = columns[2].strip()

            try:
                addr = ipaddress.IPv6Address(src_ip_str)
            except (ipaddress.AddressValueError, ValueError):
                continue

            total += 1

            if is_slaac(addr):
                print(addr)
                slaac_count += 1
            else:
                fout.write(line + "\n")
                # non_slaac.append(addr)
                # non_slaac.append(line)

    return total, non_slaac_count

def main():

    if len(sys.argv) < 2:
        print("Usage: python main.py <file1.csv.bz2> <file2.csv.bz2> ...")
        sys.exit(1)

    grand_total = 0
    grand_non_slaac = 0

    with open(FOUT, "w") as fout:
        for filepath in sys.argv[1:]:
            if not os.path.exists(filepath):
                print(f"WARNING: {filepath} not found, skipping.")
                continue
            
            print(f"Processing {filepath}...")
            total, non_slaac_count = process_file(filepath, fout)
            grand_total += total
            grand_non_slaac += non_slaac_count

if __name__ == "__main__":
    main()