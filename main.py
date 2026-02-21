import sys
import os
import bz2
import ipaddress
from collections import Counter
import datetime

now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
FOUT = now + "_non_slaac.csv"
FDUP = now + "_duplicates.csv"

# check if hex 23th-27th is fffe
def is_slaac(addr):
    full = addr.exploded.replace(":", "")
    return full[22:26].lower() == "fffe"

# get host bits of addr
def get_host(addr):
    full = addr.exploded.replace(":", "")
    return full[16:]

# write all duplicates to file
def write_duplicates(host_counter):
    with open(FOUT, "r") as fin, open(FDUP, "w") as fdup:
        for line in fin:
            line = line.strip()
            if not line:
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
            
            host_bits = get_host(addr)
            if host_counter[host_bits] > 1:
                fdup.write(line + "\n")
                dup_count += 1

    return dup_count

def process_file(filepath, fout, host_counter): 
    total = 0
    slaac_count = 0

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
                slaac_count += 1
            else:
                fout.write(line + "\n")
                host_counter[get_host(addr)] += 1
                # non_slaac.append(addr)
                # non_slaac.append(line)

    return total, slaac_count

def main():

    if len(sys.argv) < 2:
        print("Usage: python main.py <file1.csv.bz2> <file2.csv.bz2> ...")
        sys.exit(1)

    grand_total = 0
    grand_slaac_total = 0
    host_counter = Counter()

    with open(FOUT, "w") as fout:
        for filepath in sys.argv[1:]:
            if not os.path.exists(filepath):
                print(f"WARNING: {filepath} not found, skipping.")
                continue
            
            print(f"Processing {filepath}...")
            total, slaac_count = process_file(filepath, fout, host_counter)
            grand_total += total
            grand_slaac_total += slaac_count

    dup_count = write_duplicates(host_counter)

    dup_hosts = sum(1 for c in host_counter.values() if c > 1)
    most_common = host_counter.most_common(20)

    print(f"  SUMMARY")
    print(f"  Total SrcIPs across all files:   {grand_total}")
    print(f"  SLAAC (filtered out):            {grand_slaac}")
    print(f"  Duplicated host bits:            {dup_hosts}")

    print(f"  Top 20 most common host bits:")
    print(f"  {'Count':>8}  {'Host bits (last 64)':>35}")
    print(f"  {'-'*8}  {'-'*35}")
    for host, count in most_common:
        formatted = f"{host[0:4]}:{host[4:8]}:{host[8:12]}:{host[12:16]}"
        print(f"  {count:>8}  {formatted:>35}")

if __name__ == "__main__":
    main()