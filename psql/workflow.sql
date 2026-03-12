CREATE TABLE routerIPs (
    Protocol         text,       -- ICMP or TCP
    TgtIP            text,       -- ICMP probe target IP
    SrcIP            text,       -- IP of the matching probe replier 
    HopLim           smallint,   -- Hop Limit
    ICMPv6Type       smallint,   -- 8 bits (only for ICMP protocol)
    ICMPv6Code       smallint,   -- 8 bits (only for ICMP protocol)
    Flags            smallint,   -- 8 bits (only for TCP protocol)
    RTT              integer,    -- in (millieseconds)
    PfxLen           smallint,   -- subnet prefix length
    Deleted          boolean    -- flag if a row is soft deleted
    -- Entropy       float(24),  -- entropy score
    -- IPType        boolean,    -- 1 for v6 0 for v4
    -- HostID        text,       -- host id
    -- NetID         text,       -- network id
);

-- add all self-defined columns 
ALTER TABLE routerIPs ADD COLUMN Entropy float(24);
ALTER TABLE routerIPs ADD COLUMN IPType boolean;
ALTER TABLE routerIPs ADD COLUMN HostID text;
ALTER TABLE routerIPs ADD COLUMN NetID text;

-- add index on column: deleted
CREATE INDEX DeletedIndex ON routerIPs (Deleted);

-- remove aliased addresses
UPDATE routerIPs
    SET Deleted = true
    WHERE TgtIP = SrcIP;

-- mark v4 routers
UPDATE routerIPs
    SET IPType = is_v6(SrcIP)
    WHERE Deleted = false;

-- remove v4 routers
UPDATE routerIPs
    SET Deleted = true
    WHERE (IPType = false AND Deleted = false);

-- expand the rest of the router addresses
UPDATE routerIPs
    SET SrcIP = exploded(SrcIP)
    WHERE Deleted = false;

-- remove SLAAC generated addresses
UPDATE routerIPs
    SET Deleted = true
    WHERE is_slaac(SrcIP);

-- get host id
UPDATE routerIPs
    SET HostID = get_hid(SrcIP)
    WHERE Deleted = false;

-- get network id
UPDATE routerIPs
    SET NetID = get_nid(SrcIP)
    WHERE Deleted = false;

-- get entropy score for host id
UPDATE routerIPs
    SET entropy = shannon_hex(HostID)
    WHERE Deleted = false;

