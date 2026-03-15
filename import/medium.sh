#!/bin/bash

CSV="data/medium.csv"
TBL="routerIPs"
DB="psql -h localhost -p 6789"
echo "creating table $TBL"
$DB -c "CREATE TABLE $TBL (
    Protocol         text,                  -- protocol type: ICMP or TCP
    TgtIP            text,                  -- ICMP probe target IP
    SrcIP            text,                  -- IP of the replier 
    PfxLen           smallint,              -- subnet prefix length
    SubnetPfx        cidr,                  -- subnet prefix 
    Entropy          real,                  -- entropy score
    HostID           text,                  -- host id
    IDBuffer         text,                  -- network id
    HopLim           smallint,              -- Hop Limit
    ICMPv6Type       smallint,              -- 8 bits
    ICMPv6Code       smallint,              -- 8 bits
    RTT              integer,               -- round trip time (in millieseconds)
    Deleted          boolean DEFAULT false  -- flag if a row is soft deleted
);"
echo "copying file to database"
$DB -c "\COPY $TBL (Protocol, TgtIP, SrcIP, HopLim, ICMPv6Type, ICMPv6Code, RTT) FROM STDIN WITH (FORMAT csv)"< <(grep '^icmp,' "$CSV")
echo "adding subnet prefix length to database"
$DB -c "UPDATE $TBL SET PfxLen = 56;"
$DB -v tbl=$TBL -f psql/process.sql
