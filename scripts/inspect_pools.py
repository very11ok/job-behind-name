import pandas as pd

base = r"D:\harness office\research\jobtask-agent\out\objects"
for f in ["g1_jobs_2020", "g2_comm_2020", "g3_firms_2020"]:
    df = pd.read_parquet(base + "\\" + f + ".parquet")
    print(f, len(df))
    print(list(df.columns))
    print(df.head(2).to_string()[:800])
    print()

td = pd.read_parquet(r"D:\harness office\research\jobtask-agent\out\snapshots\task_dict.parquet")
print("task_dict:", len(td), list(td.columns))
print(td.head(3).to_string()[:600])
