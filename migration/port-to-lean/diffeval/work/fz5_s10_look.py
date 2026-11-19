import sys
sys.path.insert(0,"diffeval/units")
import fz5_s10_gen as g
for a,b in [(320,325),(480,485),(1195,1200),(1310,1315),(1995,2000),(2015,2020)]:
    for s in range(a,b):
        c=g.build(s)
        print(s, "mode",c["mode"],"n",c["n"],"fin",c["fin"],"icpt",c["icpt"],"coefs",c["coefs"],"cols",[(n,d) for n,d,_ in c["cols"]])
    print()
