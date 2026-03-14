Connect to PSQL:
```bash
psql -h localhost -p 6789 -U lyspfan
```

View first 30 lines:
```sql
SELECT * FROM $CSV LIMIT 30;
```

**Remove comments on top of the files before import**

## Import CSV files
Take `small.csv` as example:
```bash
CSV="data/small.csv"
TBL="smallRouterIPs"
sed -i -e 1,4d $CSV
sed -i '$d' $CSV
psql -h localhost -p 6789 -c "\COPY $TBL (Protocol, TgtIP, SrcIP, HopLim, ICMPv6Type, ICMPv6Code, RTT) FROM STDIN WITH (FORMAT csv)"< <(grep '^icmp,' "$CSV")
psql -h localhost -p 6789 -c "\COPY $TBL (Protocol, TgtIP, SrcIP, HopLim, Flags, RTT) FROM STDIN WITH (FORMAT csv)"< <(grep '^tcp,' "$CSV")
psql -h localhost -p 6789 -c "UPDATE $TBL SET PfxLen = 56;"
psql -h localhost -p 6789 -c "UPDATE $TBL SET Deleted = false;"
```

## Import compressed CSV files
Take `/mnt/usb/combined-48s-r1-s56.csv.bz2` as example:
```bash
BZ="/mnt/usb/combined-48s-r1-s56.csv.bz2"
CSV="${BZ%.bz2}"
lbzip2 -dk -n $(nproc) $BZ > /tmp/$CSV # decompress file
sed -i -e 1,4d /tmp/$CSV # strip first four lines (comments)
psql -h localhost -p 6789 -c "\COPY routerIPs (Protocol, TgtIP, SrcIP, HopLim, ICMPv6Type, ICMPv6Code, RTT) FROM STDIN WITH (FORMAT csv)"< <(grep '^icmp,' "$CSV")
psql -h localhost -p 6789 -c "\COPY routerIPs (Protocol, TgtIP, SrcIP, HopLim, Flags, RTT) FROM STDIN WITH (FORMAT csv)"< <(grep '^tcp,' "$CSV")
psql -h localhost -p 6789 -c "UPDATE routerIPs SET PfxLen = 56;"
psql -h localhost -p 6789 -c "UPDATE routerIPs SET Deleted = false;"
```

## Import CAIDA's pfx2as dataset
[Link to all datasets](https://publicdata.caida.org/datasets/routing/routeviews6-prefix2as/)
```bash
wget https://publicdata.caida.org/datasets/routing/routeviews6-prefix2as/2025/07/routeviews-rv6-20250730-0600.pfx2as.gz
gunzip routeviews-rv6-20250730-0600.pfx2as.gz
psql -h localhost -p 6789 -c "\COPY pfx2as (Prefix, PrefixLen, ASN) FROM routeviews-rv6-20250730-0600.pfx2as"
```

## Import CAIDA's as-org dataset
Preprocess data:
```bash
# dataset must be requested
FNAME="data/20250801.as-org2info.txt"
FAS="data/asfields.txt"
FORG="data/orgfields.txt"
LINE=$(grep -n "format:aut" $FNAME | cut -d ":" -f 1)
head -n $((LINE-1)) $FNAME > $FAS
sed -i '/^#/d' $FAS
sed -i 's/||/|null|/g' $FAS
tail -n +$LINE $FNAME > $FORG
sed -i '/^#/d' $FORG
sed -i 's/||/|null|/g' $FORG
```
Load data in DB:
```bash
FORG="/home/lyspfan/ipv6scan/data/orgfields.txt"
TORG="orgFields"
psql -h localhost -p 6789 -c "\COPY $TORG FROM '$FORG' WITH (DELIMITER '|', FORMAT text)"
FAS="/home/lyspfan/ipv6scan/data/asfields.txt"
TAS="asFields"
psql -h localhost -p 6789 -c "\COPY $TAS FROM '$FAS' WITH (DELIMITER '|', FORMAT text)"
```