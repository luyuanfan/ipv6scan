#!/bin/bash
CSV="data/small.csv"

# need to decompress file
# truncate first four lines in file in-place (line numbering start at 1, which is weird):
sed -i -e 1,4d data/small.csv

psql -h localhost -p 6789 -c "\COPY smallRouterIPs (Protocol, TgtIP, SrcIP, HopLim, ICMPv6Type, ICMPv6Code, RTT) FROM STDIN WITH (FORMAT csv)"< <(grep '^icmp,' "$CSV")

# load tcp rows (6 columns, with Flags, and NULL ICMPv6Type and ICMPv6Code cols)
psql -h localhost -p 6789 -c "\COPY smallRouterIPs (Protocol, TgtIP, SrcIP, HopLim, Flags, RTT) FROM STDIN WITH (FORMAT csv)"< <(grep '^tcp,' "$CSV")