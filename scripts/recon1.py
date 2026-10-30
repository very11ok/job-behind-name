import pandas as pd, os
b = r"D:\wanted\exposure\new material\total"
for y in [2016,2022,2026]:
    f = os.path.join(b,"merged",f"{y}.csv")
    df = pd.read_csv(f, encoding="utf-8", low_memory=False)
    print("===", y, "rows", len(df), "cols", len(df.columns))
    print(df.dtypes.to_string())
    for c in ["jobmatch","taskmatch","exposure","企业名称","招聘岗位","职位描述"]:
        if c in df: print(f"  {c}: nonnull={df[c].notna().sum()} nunique={df[c].nunique()}")
    print("  n_task_per_posting:", (df.groupby(["jobmatch"]).size()).describe().to_dict())
