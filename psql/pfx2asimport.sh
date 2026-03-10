#!/bin/bash
FNAME=routeviews-rv6-20250730-0600.pfx2as.gz

wget https://publicdata.caida.org/datasets/routing/routeviews6-prefix2as/2025/07/routeviews-rv6-20250730-0600.pfx2as.gz

gunzip $FNAME

psql -h localhost -p 6789 -c "\COPY pfx2as (Prefix, PrefixLen, ASN) FROM routeviews-rv6-20250730-0600.pfx2as"
