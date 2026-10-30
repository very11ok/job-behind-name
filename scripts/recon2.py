import pandas as pd
m = pd.read_csv(r"D:\wanted\exposure\new material\idmapping.csv", low_memory=False)
print("idmapping shape", m.shape, list(m.columns))
print(m.head(5).to_string())
print("---")
d = pd.read_csv(r"D:\wanted\exposure\new material\total\merged\2016.csv", low_memory=False)
print("exposure const within job?", (d.groupby("jobmatch")["exposure"].nunique()>1).mean())
print("rows per job distribution:", d.groupby("jobmatch").size().value_counts().head(10).to_dict())
