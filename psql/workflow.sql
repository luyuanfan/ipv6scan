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
    Deleted          boolean,    -- flag if a row is soft deleted
    Entropy          float(24),  -- entropy score
    HostID           text,       -- host id
    NetID            text        -- network id
);

-- add index on column: deleted 
CREATE INDEX DeletedIndex ON routerIPs (Deleted);

-- remove replies from aliased networks and v4 routers addresses
UPDATE routerIPs
    SET Deleted = true
    WHERE TgtIP = SrcIP OR NOT is_v6(SrcIP);

-- expand the rest of the router addresses
UPDATE routerIPs
    SET SrcIP = exploded(SrcIP)
    WHERE Deleted = false;

-- remove SLAAC generated addresses
UPDATE routerIPs
    SET Deleted = true
    WHERE is_slaac(SrcIP) AND Deleted = false;

-- get network id, host id, and calculate entropy score on host id
UPDATE routerIPs
    SET NetID = left(SrcIP, 16),
        HostID = right(SrcIP, 16),
        Entropy = entropy_hex(right(SrcIP, 16))
    WHERE Deleted = false;

-- CREATE VIEW myview AS
--     SELECT name, temp_lo, temp_hi, prcp, date, location
--         FROM weather, cities
--         WHERE city = name;
-- SELECT * FROM myview;

