# -*- coding: utf-8 -*-
import json, csv, io, os, sys

IN = r"D:\harness office\research\jobtask-agent\out\anno_input\2019\batch_062.csv"
OUT = r"D:\harness office\research\jobtask-agent\out\anno_output\2019\batch_062.json"

# id -> (codability, judgment, coordination, accountability, embodied, hierarchy, module)
A = {
 932:(0,1,1,1,1,"L2","生产执行"),
 23232:(1,0,1,0,0,"L0","客户服务"),
 1483:(1,1,0,0,0,"L1","工艺工程"),
 20325:(1,1,1,0,0,"L2","市场"),
 15887:(1,0,1,0,0,"L1","采购供应链"),
 10526:(1,1,0,0,1,"L1","生产执行"),
 20297:(1,1,0,0,0,"L2","工艺工程"),
 18041:(1,0,1,0,0,"L2","行政法务"),
 15276:(0,1,1,0,1,"L3","综合管理"),
 12971:(1,1,1,1,1,"L2","市场"),
 13795:(2,0,0,0,0,"L0","设备维护"),
 2809:(1,1,1,1,0,"L2","综合管理"),
 15586:(1,1,1,1,0,"L2","财务会计"),
 11427:(1,1,1,0,0,"L2","综合管理"),
 21466:(1,1,1,0,0,"L2","综合管理"),
 15667:(1,1,0,0,0,"L2","财务会计"),
 3279:(1,1,0,0,0,"L2","人力资源"),
 4615:(1,1,0,1,0,"L1","EHS安全"),
 2560:(1,1,1,0,0,"L1","客户服务"),
 12311:(1,0,0,0,1,"L0","生产执行"),
 20005:(1,1,0,1,0,"L1","EHS安全"),
 8419:(1,1,1,0,0,"L1","综合管理"),
 20059:(1,1,0,0,1,"L1","IT数据"),
 18129:(1,1,0,0,0,"L2","质量检验"),
 22085:(1,1,0,0,0,"L2","研发技术"),
 14749:(1,1,0,0,0,"L1","IT数据"),
 16070:(2,0,0,0,0,"L0","IT数据"),
 20785:(0,1,1,1,1,"L2","综合管理"),
 9753:(2,0,0,0,0,"L0","客户服务"),
 17494:(1,1,1,0,0,"L2","研发技术"),
 15805:(1,1,0,1,0,"L2","EHS安全"),
 9796:(1,1,0,0,0,"L1","IT数据"),
 21237:(1,1,1,0,0,"L2","市场"),
 8481:(1,0,0,0,1,"L0","其他"),
 7724:(1,1,1,1,1,"L1","设备维护"),
 22916:(1,0,0,1,1,"L1","EHS安全"),
 690:(1,0,1,0,1,"L0","客户服务"),
 2775:(1,1,1,0,1,"L0","行政法务"),
 9331:(1,1,0,0,0,"L1","其他"),
 21583:(0,1,1,0,1,"L2","销售"),
 12377:(1,1,0,0,1,"L0","生产执行"),
 6898:(1,1,0,0,0,"L2","研发技术"),
 11817:(1,0,0,0,1,"L1","设备维护"),
 17567:(2,0,0,0,0,"L0","EHS安全"),
 18406:(0,1,0,0,1,"L2","人力资源"),
 21988:(1,1,1,1,1,"L2","设备维护"),
 16488:(1,1,0,0,0,"L1","研发技术"),
 4273:(1,0,0,0,1,"L0","其他"),
}

with open(IN, newline='', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

keys = ["id","codability","judgment","coordination","accountability","embodied","hierarchy","module"]
out = []
for r in rows:
    i = int(r["id"])
    c,j,co,a,e,h,m = A[i]
    out.append({"id":i,"codability":c,"judgment":j,"coordination":co,"accountability":a,"embodied":e,"hierarchy":h,"module":m})

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="") as f:
    json.dump(out, f, ensure_ascii=False)

# validate
with open(OUT, encoding="utf-8") as f:
    data = json.load(f)
assert isinstance(data, list) and len(data) == len(rows), (len(data), len(rows))
for d in data:
    assert list(d.keys()) == keys, d.keys()
print("OK", len(data))
