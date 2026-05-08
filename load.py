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

full_chunk_dir="/dbdata/chunks"
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
    af_func = socket.AF_INET6
    for i, (t, s) in enumerate(zip(tgtip.values, srcip.values)):
        tgt[i] = np.frombuffer(pton_func(af_func, t), dtype=np.uint8)
        src[i] = np.frombuffer(pton_func(af_func, s), dtype=np.uint8)

    xor = np.unpackbits(tgt^src, axis=1)
    mismatch_idx = np.argmax(xor, axis=1)
    spl = mismatch_idx.astype(np.int32)
    
    full_match = ~xor.any(axis=1)
    spl[full_match] = 128
    # ignoring the case for a full match because they are aliased networks and
    # should be gone by this point
    return spl

'''
pfxlen is {56, 60, 64}
assuming home network prefix length being /56 to /64
and ISP network prefix being longer than /32 and shorter than /48
inferring by spl only works with single ISP topology
anything else should be inferred from ASN mapping

router type       code (small int)
unknown                         0
timeout                         1
homerouter                      2
upstream                        3
'''
def guess_router_type(spl, icmpv6type, icmpv6code, pfxlen):
    # timeout possibly due to routing loop
    if icmpv6type == 3:
        return 1
    # "Destination Unreachable: address unreachable"
    elif icmpv6type == 1 and icmpv6code == 3:
        # the subnet we intend to probe has something responding, so high confidence
        return 2 if spl >= pfxlen else 3
    # "Destination Unreachable: no route to destination"
    elif icmpv6type == 1 and icmpv6code == 0:
        return 2 if spl >= pfxlen else 3
    else:
        return 0

'''
policy name     code (small int)
unknown                       0
slaac_eui64                   1
bad_slaac_eui64               2
static prefix                 3
decimal                       4
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
    elif (entropy >= 0.7) and (0.375 <= ratio <= 0.625):
        return 5
    else
        return 0

def entropy_hex(hid):
    _, counts = np.unique(list(hid), return_counts=True)
    p = counts / 16.0
    return float(-np.sum(p * np.log2(p)) / log2(16))

def get_hostid(srcip):
    return binascii.hexlify(socket.inet_pton(socket.AF_INET6, srcip)).decode()[16:]

def get_netid(srcip):
    raw = socket.inet_pton(socket.AF_INET6, srcip)
    masked = raw[:8] + b'\x00' * 8
    return socket.inet_ntop(socket.AF_INET6, masked) + '/64'

def get_subnetpfx(srcip, pfxlen):
    raw = socket.inet_pton(socket.AF_INET6, srcip)
    full_bytes = pfxlen // 8
    remainder  = pfxlen  % 8
    if remainder:
        mask = 0xFF & (0xFF << (8 - remainder))
        masked = raw[:full_bytes] + bytes([raw[full_bytes] & mask]) + b'\x00' * (15 - full_bytes)
    else:
        masked = raw[:full_bytes] + b'\x00' * (16 - full_bytes)
    return socket.inet_ntop(socket.AF_INET6, masked) + f'/{pfxlen}'

'''
give each worker a connection to database
'''
def init_worker():
    global worker_conn
    worker_conn=psycopg2.connect(db_args)

'''
drop or flag rows we don't like
df is the unfiltered raw dataset
full is for full_table
small is for the ones we think are home routers
'''
def process_df(df, pfxlen):
    is_aliased = df['srcip'] == df['tgtip']                # drop aliased addresses
    is_v6 = ~df['srcip'].str.contains('.', regex=False)    # drop v4 addresses
    full = df[is_v6 & ~is_aliased].copy()                   # make a copy
    full['hostid'] = full['srcip'].map(get_hostid)           # get hostid of the rest
    full['is_slaac'] = full['hostid'].str[6:10] == 'fffe'    # mark slaac 
    full['entropy'] = [entropy_hex(h) for h in full.hostid]  # get entropy on hostid
    full['netid'] = [get_netid(s) for s in full.srcip]       # get netid
    full['subnetpfx'] = [get_subnetpfx(s, pfxlen) for s in full.srcip]
    return full

'''
take a slice, clean it, and write the filtered version to table
'''
def filter_n_copy(filepath, pfxlen):
    # read file
    read_start_t = time.time()
    colnames = ["protocol", "tgtip", "srcip", "hoplim", "icmpv6type", "icmpv6code", "rtt"]
    df = pd.read_csv(filepath, names=colnames, header=None, comment='#')

    # filter file
    filter_start_t = time.time()
    df_out = process_df(df, pfxlen)
    if df_out is None or df_out.empty: return

    copy_start_t = time.time()

    # copy to table 
    output = io.BytesIO()
    df_out.to_csv(output, sep=',', header=False, index=False)
    output.seek(0)
    cur = worker_conn.cursor()
    cur.copy_expert(f"COPY {tablename} FROM STDIN WITH (FORMAT csv, NULL '')", output)
    worker_conn.commit()
    cur.close()
    end_t = time.time()

def filter_n_copy_star(args):
    return filter_n_copy(*args)

def main():
    
    # initialize parser
    parser = argparse.ArgumentParser(
        prog="load.py",
        description="Usage: python3 load.py <tablename> --full\
                    or python3 load.py <tablename> --test"
    )
    parser.add_argument('tablename1')
    par
    parser.add_argument('--full', 
                    action='store_true')
    parser.add_argument('--force', 
                    required=False,
                    action='store_true')
    args = parser.parse_args()

    # set table name
    global tablename
    tablename = args.tablename

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
        subprocess.run(f'{dbcommand} -v tbl={tablename} -f sql/drop_table.sql', shell=True, check=True)
    subprocess.run(f'{dbcommand} -v tbl={tablename} -f sql/create_table.sql', shell=True, check=True)
    
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