CREATE TABLE IF NOT EXISTS :tbl (
    Protocol         text,
    TgtIP            inet,
    SrcIP            inet,
    HopLim           smallint,
    ICMPv6Type       smallint,
    ICMPv6Code       smallint,
    RTT              integer,
    hostid           text,
    netid            cidr,
    entropy          real,
    ratio            real,
    spl              smallint,
    router_type      smallint,
    policy           smallint
);