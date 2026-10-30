import pyarrow.parquet as pq
for f in ['out/pairs/pairs_2020.parquet', 'out/results/rule_c_adoption.parquet',
          'out/pair_judge_truth.parquet', 'out/objects/g1_jobs_2020.parquet',
          'out/objects/labels_g1_2020.parquet']:
    s = pq.read_schema(f)
    print(f)
    for n in s.names:
        print('   ', n, s.field(n).type)
    print()
