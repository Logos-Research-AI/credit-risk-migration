"""INV03: Python float x ** 2 versus x * x (not bit-identical on this platform)."""
import numpy as np, math
rng=np.random.default_rng(0); v=np.concatenate([rng.standard_normal(200000)*10.0**rng.integers(-150,150,200000), rng.random(100000), rng.standard_normal(100000)*50])
bad=[float(t) for t in v if float(t)**2!=float(t)*float(t)]
print(len(bad), len(v), bad[:5], [(t**2, t*t) for t in bad[:3]])
print("in [1e-100,1e100]:", sum(1 for t in bad if 1e-100<abs(t)<1e100))
try: print(1e200**2)
except Exception as e: print(repr(e))
print(1e200*1e200, (1e-200)**2, np.float64(1e200)**2)
