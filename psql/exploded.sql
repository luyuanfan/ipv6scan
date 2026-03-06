CREATE FUNCTION exploded(src_ip_str text)
  RETURNS text
AS $$
  import ipaddress
  src_ip_obj = ipaddress.IPv6Address(src_ip_str)
  full_addr = src_ip_obj.exploded.replace(":", "")
  return full_addr
$$ LANGUAGE plpython3u;