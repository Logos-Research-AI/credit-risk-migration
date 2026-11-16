# joins work/t16_run.o<i>.txt (one eval output each) into work/t16_run.out.txt
cd "$(dirname "$0")/../work" && : > t16_run.out.txt && for i in 0 1 2 3; do if [ -s t16_run.o$i.txt ]; then tr -d '\n' < t16_run.o$i.txt >> t16_run.out.txt; echo >> t16_run.out.txt; else echo "ERROR not run" >> t16_run.out.txt; fi; done
