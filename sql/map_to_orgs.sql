-- mapping each duplicated hostid prefix to asn and organziation ####

create materialized view if not exists dups_t_mapped as
select distinct on (d.hostid, d.netid)
    d.*,
    p.prefix as caida_pfx,
    p.asn as asn,
    p.orgname as orgname,
    p.orgid,
    p.country
from dups_t d
left join pfx2as2org p on p.prefix >>= d.netid
order by d.hostid, d.netid, p.prefixlen desc nulls last;