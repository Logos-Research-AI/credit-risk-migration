# joins work/t13_ks.o<i>.txt (one eval output each) into work/t13_ks.out.txt and compares
cd "$(dirname "$0")/../work" && : > t13_ks.out.txt && for i in 0 1 2 3 4 5 6 7; do if [ -s t13_ks.o$i.txt ]; then tr -d '\n' < t13_ks.o$i.txt >> t13_ks.out.txt; echo >> t13_ks.out.txt; else echo "ERROR not run" >> t13_ks.out.txt; fi; done
