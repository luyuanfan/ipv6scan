CREATE FUNCTION shannon_bin(hid text)
  RETURNS float
AS $$
  from collections import Counter
  from math import log2
  binary = bin(int(hid, 16))[2:].zfill(64)
  c = Counter(binary)
  score = - sum([(c[val] / 64) * log2(c[val] / 64) for val in c.keys()])
  return score
$$ LANGUAGE plpython3u;