import csv, json, os, io

src = r"D:\harness office\research\jobtask-agent\out\anno_input\2019\batch_091.csv"
dst = r"D:\harness office\research\jobtask-agent\out\anno_output\2019\batch_091.json"

ann = {
3154:  (1,0,0,1,1,"L0","财务会计"),
8504:  (1,1,0,0,0,"L2","研发技术"),
15725: (1,1,1,1,0,"L3","综合管理"),
11951: (0,0,0,0,1,"L0","设备维护"),
15372: (1,1,1,1,0,"L2","EHS安全"),
17800: (0,0,0,0,1,"L0","设备维护"),
1811:  (1,1,1,1,1,"L1","采购供应链"),
23536: (0,0,0,0,1,"L0","其他"),
1214:  (1,1,1,1,0,"L2","行政法务"),
17894: (1,1,1,1,0,"L2","EHS安全"),
13779: (1,1,1,1,0,"L1","客户服务"),
41:    (1,1,1,0,0,"L2","研发技术"),
11085: (1,1,0,1,1,"L1","设备维护"),
22078: (1,1,1,1,0,"L2","研发技术"),
4298:  (1,0,1,0,1,"L0","设备维护"),
21533: (1,0,0,1,0,"L0","财务会计"),
9018:  (0,1,1,1,0,"L2","其他"),
19649: (1,1,1,0,0,"L2","财务会计"),
11021: (0,1,1,0,0,"L2","其他"),
22227: (1,1,0,0,0,"L1","IT数据"),
7666:  (1,1,1,1,0,"L2","综合管理"),
23119: (1,0,0,0,1,"L0","客户服务"),
1412:  (0,1,1,0,1,"L2","工艺工程"),
15807: (1,1,1,1,0,"L2","EHS安全"),
14707: (1,1,1,0,0,"L1","IT数据"),
21841: (0,1,1,1,0,"L2","行政法务"),
9700:  (1,0,0,0,0,"L1","销售"),
20189: (0,1,1,1,1,"L2","销售"),
23739: (0,1,1,1,1,"L1","物流仓储"),
14637: (0,1,1,1,0,"L3","综合管理"),
18074: (1,1,0,1,0,"L2","EHS安全"),
22095: (0,1,0,0,1,"L1","设备维护"),
4028:  (0,1,1,0,0,"L2","销售"),
18170: (1,0,1,0,0,"L1","生产执行"),
13956: (1,0,0,0,1,"L0","生产执行"),
5047:  (0,1,1,0,0,"L1","人力资源"),
16153: (1,1,1,1,0,"L2","人力资源"),
21729: (0,1,1,0,1,"L2","销售"),
20280: (2,0,0,0,0,"L0","行政法务"),
21746: (1,1,1,1,0,"L2","IT数据"),
18148: (1,1,0,1,1,"L2","EHS安全"),
9239:  (1,1,1,1,0,"L2","综合管理"),
20906: (2,0,0,0,1,"L0","物流仓储"),
23563: (1,0,1,0,1,"L0","生产执行"),
14249: (0,1,1,0,1,"L1","其他"),
17664: (1,1,1,0,0,"L1","销售"),
3481:  (1,1,1,1,0,"L2","IT数据"),
4565:  (1,1,1,0,0,"L1","其他"),
}

MODULES = {"生产执行","质量检验","研发技术","工艺工程","设备维护","销售","市场","采购供应链","物流仓储","人力资源","财务会计","行政法务","IT数据","EHS安全","客户服务","综合管理","其他"}

rows = []
with open(src, "r", encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        rows.append((int(r["id"]), r["text"]))

out = []
missing = []
for i, (rid, text) in enumerate(rows):
    a = ann.get(rid)
    if a is None:
        missing.append(rid); continue
    c, j, co, ac, em, h, m = a
    assert c in (0,1,2) and j in (0,1) and co in (0,1) and ac in (0,1) and em in (0,1)
    assert h in ("L0","L1","L2","L3") and m in MODULES, (rid, m)
    out.append({"id": rid, "codability": c, "judgment": j, "coordination": co,
                "accountability": ac, "embodied": em, "hierarchy": h, "module": m})

if missing:
    raise SystemExit("missing ids: %s" % missing)
if len(out) != len(rows):
    raise SystemExit("count mismatch: %d vs %d" % (len(out), len(rows)))

os.makedirs(os.path.dirname(dst), exist_ok=True)
with open(dst, "w", encoding="utf-8", newline="") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("CSV rows:", len(rows), "JSON items:", len(out))
