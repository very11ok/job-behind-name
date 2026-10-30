import pandas as pd
d = pd.read_csv(r"D:\wanted\exposure\new material\total\merged\2016.csv", low_memory=False)
print("dup (job,task) pairs:", d.duplicated(["jobmatch","taskmatch"]).sum(), "of", len(d))
print("exposure nunique per task:", (d.groupby("taskmatch")["exposure"].nunique()>1).sum())
print("exposure per (job,task) nunique>1:", (d.groupby(["jobmatch","taskmatch"])["exposure"].nunique()>1).sum())
print("exposure describe:", d.exposure.describe().to_dict())
print("n distinct exposure per job (mean):", d.groupby("jobmatch")["exposure"].nunique().mean())
print(d[["jobmatch","taskmatch","exposure"]].drop_duplicates().head(10).to_string())
