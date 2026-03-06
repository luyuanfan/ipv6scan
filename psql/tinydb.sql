CREATE TABLE tinyRouterIPs (
    ReplyType        boolean,    -- 1 for ICMP 0 for TCP
    TgtIP            text,       -- inet datatype ain't too versatile
    SrcIP            text,       -- inet datatype ain't too versatile
    HopLim           smallint,   -- depends, prolly won't go over 32767
    ICMPv6Type       smallint,   -- 8 bits
    ICMPv6Code       smallint,   -- 8 bits
    Flags            smallint,   -- 8 bits
    RTT              integer,    -- in (millieseconds)
    Entropy          float(24),  -- entropy score
    PfxLen           integer,    -- which subnet it's sitting on
    V6Router         boolean     -- 1 for yes 0 for no
    -- might keep one file marking whether responding router uses v4 or v6
);

INSERT INTO tinyRouterIPs VALUES (true, '2607:5380:1470:be58:8647:6e47:456e:bfc2', '2607:5380:8000:3e:1621:3ff:fedf:2ba8', 48, 1, 0, NULL, 125, NULL, 48, true);

INSERT INTO tinyRouterIPs VALUES (true, '2607:fa49:1c42:3f18:8647:6e47:456e:bfc2', '2607:fa48:c:9500:64c2:882:e885:89bb', 46, 1, 0, NULL, 125, NULL, 48, true);

INSERT INTO tinyRouterIPs VALUES (true, '2a01:cb08:9150:4a2b:8647:6e47:456e:bfc2', '2a01:cb08:9150:4a00:c2d7:aaff:febf:34f1', 239, 1, 0, NULL, 197, NULL, 48, true);