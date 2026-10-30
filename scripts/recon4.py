import pandas as pd
p = r"D:\wanted\exposure\new material"
for f, name in [
  (p+r"\community\dict\onet_tasks.csv","onet_tasks"),
  (p+r"\gpt4_exposure\task exposure\2016_task.csv","task_exposure_2016"),
  (p+r"\gpt4_exposure\job exposure\2016_job.csv","job_exposure_2016"),
  (p+r"\community\analysis\E_community_profile.csv","community_profile"),
  (p+r"\newjob\2017new.csv","2017new"),
]:
    try:
        d = pd.read_csv(f, low_memory=False, nrows=5, encoding="utf-8")
        full = sum(1 for _ in open(f, encoding="utf-8", errors="ignore"))-1
        print("===",name,"rows~",full,"cols",list(d.columns))
        print(d.head(3).to_string()[:1200])
    except Exception as e:
        print("===",name,"ERR",e)
