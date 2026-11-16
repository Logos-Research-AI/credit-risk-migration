#!/bin/sh
# usage (from migration/port-to-lean): sh diffeval/work/assemble.sh <suite> <n inputs>
# joins diffeval/work/<suite>.out<k>.txt into <suite>.out.txt (a missing one is an ERROR line)
s=diffeval/work/$1; n=$2; : > $s.out.txt
k=0; while [ $k -lt $n ]; do if [ -s $s.out$k.txt ]; then tr -d '\n' < $s.out$k.txt >> $s.out.txt; echo >> $s.out.txt; else echo "ERROR not run" >> $s.out.txt; fi; k=$((k+1)); done
