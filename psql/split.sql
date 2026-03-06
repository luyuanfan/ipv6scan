CREATE FUNCTION get_hid(addr text)
  RETURNS text
AS $$
  return addr[16:]
$$ LANGUAGE plpython3u;

CREATE FUNCTION get_nid(addr text)
  RETURNS text
AS $$
  return addr[:16]
$$ LANGUAGE plpython3u;