CREATE FUNCTION is_slaac(addr text)
  RETURNS boolean
AS $$
  return addr[22:26].lower() == "fffe"
$$ LANGUAGE plpython3u;