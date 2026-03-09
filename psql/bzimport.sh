#!/bin/bash
BZ="/mnt/usb/combined-48s-r1-s56.csv.bz2"
CSV="${BZ%.bz2}"

# decompress file (lbzip2 is the multithreaded version of bzip)
lbzip2 -dk -n $(nproc) $BZ > /tmp/$CSV

# truncate first four lines in file in-place (line numbering start at 1, which is weird): 
sed -i -e 1,4d /tmp/$CSV

# load icmp rows (7 columns, with ICMPv6Type, ICMPv6Code, and NULL Flags col)
psql -c "\COPY routerIPs (Protocol, TgtIP, SrcIP, HopLim, ICMPv6Type, ICMPv6Code, RTT) FROM STDIN WITH (FORMAT csv)"< <(grep '^icmp,' "$CSV")

# load tcp rows (6 columns, with Flags, and NULL ICMPv6Type and ICMPv6Code cols)
psql -c "\COPY routerIPs (Protocol, TgtIP, SrcIP, HopLim, Flags, RTT) FROM STDIN WITH (FORMAT csv)"< <(grep '^tcp,' "$CSV")

rm "$CSV"