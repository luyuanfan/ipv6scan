################### dup_hostids_table ####################

create index if not exists dup_hostids_table_idx on dup_hostids_table (hostid);

create materialized view bad_slaac_hids as
select * from dup_hostids_table
where 
    substring(hostid from 7 for 5) <> 'ff0fe' or
    substring(hostid from 7 for 5) <> 'ff0f0' or 
    substring(hostid from 5 for 6) <> 'eeff0f';

####################### filtered_t #######################

select count (*) from filtered_t;

create index if not exists hostid_idx on filtered_t (hostid);
create index if not exists netid_idx on filtered_t (netid);
create index if not exists router_type_idx on filtered_t (router_type);

####################### unique_repliers #######################

create table if not exists unique_repliers as
select distinct on (hostid, netid) *
from filtered_t
order by hostid, netid, rtt asc;

create index if not exists ur_hostid_idx on unique_repliers (hostid);
create index if not exists ur_netid_idx on unique_repliers (netid);
create index if not exists ur_router_type_idx on unique_repliers (router_type);

# after removing the srcips that replied multiple times, 
# we have a set of repliers who are SLAAC w PE homerouters
select count (hostid) as unique_repliers_count from unique_repliers;

####################### dups_t #######################

# get the unique repliers whose hostid portion is repeated at least two times
create table if not exists dups_t as
with qualifying_hostids as (
    select
        hostid,
        count(*) as total,
        count(distinct netid) as netid_count
    from unique_repliers
    group by hostid
    having count(distinct netid) > 1
)
select
    f.*,
    q.total,
    q.netid_count
from unique_repliers f
inner join qualifying_hostids q on f.hostid = q.hostid;

create index if not exists dups_t_hostid_idx on dups_t (hostid);
create index if not exists dups_t_netid_idx on dups_t (netid);
create index if not exists dups_t_netid_gist_idx ON dups_t USING gist (netid inet_ops);
create index if not exists dups_t_dups_idx on dups_t (netid_count);

# get set of dups (for counting how many collision happened)
create materialized view if not exists dup_hostid_set as 
select distinct hostid
from dups_t;

# count percentage of each {1,2,...,N}-way collision among all
create materialized view if not exists collision_distribution as
with per_hostid as (
    select distinct hostid, netid_count from dups_t
)
select
    netid_count as n_way,
    count(*) as num_iids,
    count(*) * 100.0 / sum(count(*)) over () as percentage
from per_hostid
group by netid_count
order by netid_count;

####################### dups_t_mapped #######################

# map all repliers to AS
# pick the most specific match (max prefix length)
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

create index if not exists dups_t_mapped_hostid_idx on dups_t_mapped (hostid);
create index if not exists dups_t_mapped_netid_idx on dups_t_mapped (netid);
create index if not exists dups_t_mapped_netid_count_idx on dups_t_mapped (netid_count);
create index if not exists dups_t_mapped_asn_idx on dups_t_mapped (asn);
create index if not exists dups_t_mapped_orgname_idx on dups_t_mapped (orgname);

create materialized view if not exists orgs_with_dups as
select
from dups_t_mapped;


####################### grouped_t #######################

# key dataset on hostid; get a sense of where these hostids are coming from
create materialized view if not exists grouped_t as
with hostid_stats as (
    select
        hostid,
        count(distinct netid) as unique_net_count,
        array_agg(distinct netid) as unique_net_set,
        count(distinct asn) as unique_asn_count,
        array_agg(distinct asn) as unique_asn_set,
        count(distinct orgname) as unique_orgs_count,
        array_agg(distinct orgname) as unique_orgs_set,
        count(distinct country) as unique_country_count,
        array_agg(distinct country) as unique_country_set
    from dups_t_mapped
    group by hostid
),
hostid_asn_stats as (
    select
        hostid,
        asn,
        count(distinct netid) as distinct_netids
    from dups_t_mapped
    group by hostid, asn
),
hostid_asn_rollup as (
    select
        hostid,
        jsonb_agg(
            jsonb_build_object(
                'asn', asn,
                'count', distinct_netids
            )
        ) as info
    from hostid_asn_stats
    group by hostid
)
select
    h.*,
    r.info
from hostid_stats h
inner join hostid_asn_rollup r on r.hostid = h.hostid;

create index if not exists grouped_t_hostid_idx on grouped_t (hostid);


####################### dups_t_mapped (but reworked) #######################
create table if not exists grouped_t_reworked as
select
    *
from grouped_t
where
    'Nova Telecommunications & Media Single Member S.A' <> ALL(unique_orgs_set) and
    hostid not like '%0000%' and
    hostid not like '00010%';

create index if not exists grouped_t_reworked_idx on grouped_t_reworked (hostid);

create table if not exists grouped_t_reworked_two as
select
    *
from grouped_t_reworked
where
    hostid not like '00010%';

create index if not exists grouped_t_reworked_two_idx on grouped_t_reworked_two (hostid);

##################### counting ######################

# out of the two-way collisions, how many are from within an AS
# how many are starting with four zeros
# 9607623
select count (*) from grouped_t_reworked_two;

# 5418743
select count (*) from grouped_t_reworked_two where unique_net_count = 2;

select round((count(*) * 100.0 / 5418743), 2) as pct
from grouped_t_reworked_two
where unique_net_count = 2 and unique_asn_count = 1;

select round((count(*) * 100.0 / 5418743), 2) as pct
from grouped_t_reworked_two
where unique_net_count = 2 and unique_orgs_count = 1;

create materialized view collision_across_ases as
select *
from grouped_t
where unique_asn_count > 1;

create materialized view collision_across_ases as
select *
from grouped_t
where unique_asn_count > 1;

SELECT DISTINCT asn, autname, orgname, country
FROM pfx2as2org
WHERE asn IN (
    '28219', '262566', '262979', '268085', '262663',
    '264050', '267345', '274799', '262669', '28343',
    '268126', '267944', '270303', '272599', '272489',
    '263356', '264921', '267012', '266951', '270305',
    '267194', '262311', '266616', '269535', '262880',
    '264118', '263099', '272434', '273366', '262535'
)
ORDER BY asn;