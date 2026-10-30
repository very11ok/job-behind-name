import pyarrow.parquet as pq
for f in ['out/objects/g2_comm_2020.parquet',
          'out/objects/labels_g2_2020.parquet',
          'out/objects/judge_g2_2020.parquet',
          'out/snapshots/jobs_2020.parquet',
          'out/snapshots/task_dict.parquet',
          'out/snapshots/edges_2020.parquet']:
    s = pq.read_schema(f)
    print(f)
    for n in s.names:
        print('   ', n, s.field(n).type)
    print()
