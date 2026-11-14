import sys, json
rows = json.load(open(sys.argv[1]))
with open('/Users/cristophersalvi/GitHub/sas-migration/migration/inventory.proc.tsv', 'a') as f:
    for r in rows:
        assert len(r) == 7, r[:2]
        for x in r:
            assert '\t' not in x and '\n' not in x, r[:2]
        f.write('\t'.join(r) + '\n')
print('appended', len(rows))
