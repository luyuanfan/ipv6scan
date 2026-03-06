CREATE TABLE tinyRouterIPs (
    Protocol         boolean,    -- 1 for ICMP 0 for TCP
    TgtIP            text,       -- inet datatype ain't too versatile
    SrcIP            text,       -- inet datatype ain't too versatile
    HostID           text,       -- host id of SrcIP
    NetID            text,       -- network of SrcIP
    HopLim           smallint,   -- depends, prolly won't go over 32767
    ICMPv6Type       smallint,   -- 8 bits
    ICMPv6Code       smallint,   -- 8 bits
    Flags            smallint,   -- 8 bits
    RTT              integer,    -- in (millieseconds)
    Entropy          float(24),  -- entropy score
    PfxLen           integer,    -- which subnet it's sitting on
    RouterType       boolean     -- 1 for yes 0 for no
    -- might keep one file marking whether responding router uses v4 or v6
);

CREATE EXTENSION plpython3u;

INSERT INTO tinyRouterIPs VALUES (true, '2607:5380:1470:be58:8647:6e47:456e:bfc2', '2607:5380:8000:3e:1621:3ff:fedf:2ba8', NULL, NULL, 48, 1, 0, NULL, 125, NULL, 48, true);
INSERT INTO tinyRouterIPs VALUES (true, '2607:fa49:1c42:3f18:8647:6e47:456e:bfc2', '2607:fa48:c:9500:64c2:882:e885:89bb', NULL, NULL, 46, 1, 0, NULL, 125, NULL, 48, true);
INSERT INTO tinyRouterIPs VALUES (true, '2a01:cb08:9150:4a2b:8647:6e47:456e:bfc2', '2a01:cb08:9150:4a00:c2d7:aaff:febf:34f1', NULL, NULL, 239, 1, 0, NULL, 197, NULL, 48, true);

CREATE FUNCTION exploded(src_ip_str text)
  RETURNS text
AS $$
  import ipaddress
  src_ip_obj = ipaddress.IPv6Address(src_ip_str)
  full_addr = src_ip_obj.exploded.replace(":", "")
  return full_addr
$$ LANGUAGE plpython3u;

UPDATE tinyRouterIPs SET SrcIP = exploded(SrcIP);


CREATE FUNCTION shannon_bin(hid text)
  RETURNS float
AS $$
  from collections import Counter
  from math import log2
  binary = bin(int(hid, 16))[2:].zfill(64)
  c = Counter(binary)
  score = - sum([(val / 64) * log2(val / 64) for key, val in c.items()])
  return score
$$ LANGUAGE plpython3u;

UPDATE tinyRouterIPs SET entropy = shannon_bin(SrcIP);