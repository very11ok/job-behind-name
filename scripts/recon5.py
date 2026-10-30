import pandas as pd
p = r"D:\wanted\exposure\new material\total\newjob"
d = pd.read_csv(p+r"\2017new.csv", low_memory=False, nrows=4)
print("2017new cols:", list(d.columns)); print(d.to_string()[:800])
f = pd.read_csv(p+r"\first_appear.csv")
print("first_appear:", f.shape, f.date.value_counts().sort_index().to_dict())
mm = pd.read_csv(r"D:\wanted\exposure\new material\gpt4_exposure\task minmax\2016_task.csv", nrows=3)
print("task minmax cols:", list(mm.columns)); print(mm.head(3).to_string()[:600])
b = pd.read_csv(r"D:\wanted\exposure\new material\community\analysis\B_herding.csv")
print("B_herding:", b.shape, list(b.columns)); print(b.head(6).to_string()[:900])
