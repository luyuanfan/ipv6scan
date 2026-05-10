create index if not exists hostid_idx on filtered_t (hostid);
create index if not exists netid_idx on filtered_t (netid);
create index if not exists router_type_idx on filtered_t (router_type);

-- create a table on just the host ids that are duplicated
create table if not exists dups_t as
with qualifying_hostids as (
    select
        hostid,
        count(*) as total,
        count(distinct netid) as netid_count
    from filtered_t
    group by hostid
    having count(distinct netid) > 1
)
select
    f.*,
    q.total,
    q.netid_count
from filtered_t f
inner join qualifying_hostids q on f.hostid = q.hostid;

create index if not exists dups_t_hostid_idx on dups_t (hostid);
create index if not exists dups_t_netid_idx on dups_t (netid);
create index if not exists dups_t_netid_gist_idx ON dups_t USING gist (netid inet_ops);

