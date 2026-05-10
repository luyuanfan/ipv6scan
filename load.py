import os
import io
import re
import time
import socket
import binascii
import argparse
import psycopg2 
import subprocess
import numpy as np
import pandas as pd
from math import log2
from tqdm import tqdm
import multiprocessing as mp
from scipy.stats import entropy

full_chunk_dir="/mnt/chunks"
test_chunk_dir="data/chunks"
nproc=40
dbcommand="psql -h localhost -p 6789"
db_args = "host=localhost port=6789 dbname=lyspfan user=lyspfan password=lyspfan"
_BAD_PFX = re.compile(r'^(00000|00010000|00010001|00010002|00020001|00020002|80000|96e3eeff0f)')
_ALL_DIGS = re.compile(r'^[0-9]{16}$')

'''
get shared prefix length to determine if tgt and src are in the same ISP
'''
def get_shared_prefix_length(tgtip, srcip):
    n = len(tgtip)
    tgt = np.empty((n, 16), dtype=np.uint8)
    src = np.empty((n, 16), dtype=np.uint8)
    pton_func = socket.inet_pton
    fam6 = socket.AF_INET6
    for i, (t, s) in enumerate(zip(tgtip.values, srcip.values)):
        tgt[i] = np.frombuffer(pton_func(fam6, t), dtype=np.uint8)
        src[i] = np.frombuffer(pton_func(fam6, s), dtype=np.uint8)

    xor = np.unpackbits(tgt^src, axis=1)
    mismatch_loc = np.argmax(xor, axis=1)
    spl = mismatch_loc.astype(np.int32)

    # full matches shouldn't exist because they are from aliased networks
    # and should be gone by this point but still
    full_match = ~xor.any(axis=1)
    spl[full_match] = 128
    return spl

'''
pfxlen is {56, 60, 64}
assuming home network prefix length being /56 to /64
and ISP network prefix being longer than /32 and shorter than /48
anything else should be inferred from ASN mapping

router type       code (small int)
unknown                         0
timeout                         1
homerouter                      2
upstream                        3
'''
def guess_router_type(spl, icmpv6type, icmpv6code, pfxlen):
    # "Time Exceeded"
    if icmpv6type == 3:
        return 1
    # "Destination Unreachable: address unreachable"
    elif icmpv6type == 1 and icmpv6code == 3:
        return 2 if spl >= 56 else 3
    # "Destination Unreachable: no route to destination"
    elif icmpv6type == 1 and icmpv6code == 0:
        return 2 if spl >= 56 else 3
    else:
        return 0

'''
policy name     code (small int)
unknown                       0
slaac_eui64                   1
bad_slaac_eui64               2
static prefix                 3
digit only                    4
slaac_pe                      5
'''
def guess_policy(hid, entropy, ratio):
    if _ALL_DIGS.match(hid):
        return 4
    if hid[6:10] == "fffe":
        return 1
    elif hid[6:11] == "ff0fe" or hid[6:11] == "ff0f0":
        return 2
    elif _BAD_PFX.match(hid):
        return 3
    elif (entropy >= 0.65) or (0.375 <= ratio <= 0.625):
        return 5
    else:
        return 0

def vec_entropy_n_ratio(hid):
    n = len(hid)
    chars = np.frombuffer(''.join(hid).encode('ascii'), dtype=np.uint8).reshape(n, 16)
    counts = np.zeros((n, 16), dtype=np.float64)
    for i, c in enumerate('0123456789abcdef'):
        counts[:, i] = (chars == ord(c)).sum(axis=1)

    p = counts / 16.0
    with np.errstate(divide='ignore', invalid='ignore'):
        log_p = np.where(p > 0, np.log2(p), 0.0)
        entropy = -(p * log_p).sum(axis=1) / np.log2(16)

    nibble_popcount = np.array([bin(i).count('1') for i in range(16)], dtype=np.float64)
    ratio = (counts @ nibble_popcount) / 64.0

    return entropy, ratio

def vec_get_hostid_n_netid(srcip):
    pton, ntop, af = socket.inet_pton, socket.inet_ntop, socket.AF_INET6
    hid, nid = [], []
    for s in srcip.values:
        raw = pton(af, s)
        hid.append(raw[8:].hex())
        nid.append(ntop(af, raw[:8] + b'\x00' * 8) + '/64')
    return hid, nid

'''
give each worker a connection to database
'''
def init_worker():
    global worker_conn
    worker_conn=psycopg2.connect(db_args)

'''
drop or flag rows we don't like
df is the unfiltered raw dataset
big - all non-v4/non-aliased entries with annotation
small - all entries that we think are from home routers using slaac w pe
'''
def process_df(df, pfxlen):
    is_aliased = df['srcip'] == df['tgtip']                  # drop aliased addresses
    is_v6 = ~df['srcip'].str.contains('.', regex=False)      # drop v4 addresses
    big = df[is_v6 & ~is_aliased].copy()                     # make a copy

    big['hostid'], big['netid'] = vec_get_hostid_n_netid(big['srcip'])             
    big['entropy'], big['ratio'] = vec_entropy_n_ratio(big['hostid'])

    big['spl'] = get_shared_prefix_length(big['tgtip'], big['srcip'])
    big['router_type'] = [
        guess_router_type(spl, t, c, pfxlen)
        for spl, t, c in zip(big['spl'], big['icmpv6type'], big['icmpv6code'])
    ]
    big['policy'] = [
        guess_policy(h, e, r)
        for h, e, r in zip(big['hostid'], big['entropy'], big['ratio'])
    ]

    small = big[(big['router_type'] != 1) & (big['policy'] == 5)]
    return big, small

'''
take a slice, clean it, and write the filtered version to table
'''
def filter_n_copy(filepath, pfxlen):
    # read file
    colnames = ["protocol", "tgtip", "srcip", "hoplim", "icmpv6type", "icmpv6code", "rtt"]
    df = pd.read_csv(filepath, names=colnames, header=None, comment='#')

    # filter file
    big, small = process_df(df, pfxlen)
    if big is None or big.empty: return

    # copy to table 
    cur = worker_conn.cursor()
    for tbl, frame in [(full_table, big), (filtered_table, small)]:
        if frame.empty:
            continue
        buf = io.BytesIO()
        frame.to_csv(buf, sep=',', header=False, index=False)
        buf.seek(0)
        cur.copy_expert(f"COPY {tbl} FROM STDIN WITH (FORMAT csv, NULL '')", buf)
    worker_conn.commit()
    cur.close()

def filter_n_copy_star(args):
    return filter_n_copy(*args)

def main():
    
    # initialize parser
    parser = argparse.ArgumentParser(
        prog="load.py",
        description="Usage: python3 load.py <full_table> <filtered_table> --full\
                    or python3 load.py <full_table> <filtered_table> --test"
    )
    parser.add_argument('full_table')
    parser.add_argument('filtered_table')
    parser.add_argument('--full', 
                    action='store_true')
    parser.add_argument('--force', 
                    required=False,
                    action='store_true')
    args = parser.parse_args()

    # set table name
    global full_table
    global filtered_table
    full_table, filtered_table = args.full_table, args.filtered_table

    # create a list of all files to load
    chunk_dir = full_chunk_dir if args.full else test_chunk_dir
    pathlist = []
    pfxlenlist = []
    for file in os.listdir(chunk_dir):
        if file.endswith('.csv'):
            pathlist.append(os.path.join(chunk_dir, file))
            pfxlenlist.append(int(file.removesuffix('.csv')[-2:]))
    args_list = list(zip(pathlist, pfxlenlist))

    # if using --force, remove the existing table and create a new one from scratch
    if (args.force == True):
        subprocess.run(f'{dbcommand} -v tbl={full_table} -f sql/drop_table.sql', shell=True, check=True)
        subprocess.run(f'{dbcommand} -v tbl={filtered_table} -f sql/drop_table.sql', shell=True, check=True)
    subprocess.run(f'{dbcommand} -v tbl={full_table} -f sql/create_table.sql', shell=True, check=True)
    subprocess.run(f'{dbcommand} -v tbl={filtered_table} -f sql/create_table.sql', shell=True, check=True)
    
    start_full = time.time()
    pbar = tqdm(total=len(args_list))

    # create workers and let them do work
    pool = mp.Pool(nproc, init_worker)
    try:
        for _ in pool.imap_unordered(filter_n_copy_star, args_list):
            pbar.update()
    finally:
        pool.close()
        pool.join()
        pbar.close()

    end_full = time.time()
    print(f"All done in {end_full-start_full:.2f}s")

if __name__ == "__main__":
    main()