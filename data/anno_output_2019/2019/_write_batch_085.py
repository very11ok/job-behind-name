import csv, json, os

SRC = r"D:\harness office\research\jobtask-agent\out\anno_input\2019\batch_085.csv"
DST = r"D:\harness office\research\jobtask-agent\out\anno_output\2019\batch_085.json"

rows = []
with open(SRC, "r", encoding="utf-8-sig", newline="") as f:
    r = csv.DictReader(f)
    for row in r:
        rows.append(row)

labels = {
2291:  (0,0,0,0,1,"L0","生产执行"),
7787:  (0,1,1,1,0,"L2","其他"),
8567:  (1,1,0,0,1,"L1","物流仓储"),
839:   (0,1,1,1,0,"L2","综合管理"),
3122:  (1,0,0,0,1,"L0","生产执行"),
22658: (0,1,1,0,0,"L2","市场"),
16976: (1,1,0,0,0,"L2","研发技术"),
17067: (0,1,0,1,1,"L1","其他"),
13612: (1,0,0,0,1,"L0","生产执行"),
16259: (1,1,0,0,0,"L1","IT数据"),
15234: (1,0,1,0,0,"L0","行政法务"),
13099: (0,1,0,1,1,"L2","行政法务"),
13155: (0,1,1,0,0,"L1","客户服务"),
18919: (1,1,1,1,0,"L2","综合管理"),
11375: (1,1,1,1,0,"L2","生产执行"),
21874: (0,1,1,1,0,"L2","EHS安全"),
9354:  (1,0,1,0,0,"L0","行政法务"),
23656: (0,1,0,1,1,"L1","EHS安全"),
21676: (1,1,0,0,0,"L1","IT数据"),
8416:  (0,1,0,1,1,"L1","设备维护"),
9410:  (0,1,0,1,1,"L1","设备维护"),
16576: (0,1,1,0,0,"L2","客户服务"),
11294: (0,1,1,0,0,"L1","财务会计"),
22045: (1,0,0,1,1,"L1","生产执行"),
19624: (0,1,1,1,1,"L2","EHS安全"),
3352:  (0,1,1,1,0,"L2","行政法务"),
21420: (0,1,1,1,1,"L2","其他"),
727:   (0,1,1,0,1,"L1","客户服务"),
5320:  (1,1,0,1,0,"L2","IT数据"),
4000:  (0,1,0,0,0,"L1","其他"),
18584: (1,0,1,0,0,"L1","采购供应链"),
8515:  (0,1,0,1,1,"L1","生产执行"),
2227:  (1,0,0,0,1,"L0","生产执行"),
3214:  (2,0,0,0,0,"L0","物流仓储"),
10878: (0,1,1,1,1,"L2","行政法务"),
14694: (1,1,0,0,0,"L1","IT数据"),
306:   (0,1,0,0,0,"L1","市场"),
8544:  (2,0,0,0,1,"L0","生产执行"),
1772:  (0,1,1,0,1,"L2","客户服务"),
17746: (1,1,0,1,1,"L1","质量检验"),
4206:  (1,0,0,0,0,"L0","行政法务"),
21718: (0,1,1,0,0,"L2","IT数据"),
9993:  (0,1,0,1,1,"L1","设备维护"),
2644:  (1,0,0,0,1,"L0","其他"),
10276: (0,1,0,0,1,"L1","生产执行"),
20157: (1,0,0,1,1,"L0","质量检验"),
23728: (1,0,0,0,1,"L0","设备维护"),
20589: (0,1,1,1,1,"L1","EHS安全"),
}

MODULES = {"生产执行","质量检验","研发技术","工艺工程","设备维护","销售","市场","采购供应链","物流仓储","人力资源","财务会计","行政法务","IT数据","EHS安全","客户服务","综合管理","其他"}

out = []
for row in rows:
    i = int(row["id"])
    c, j, co, a, e, h, m = labels[i]
    assert m in MODULES, m
    assert c in (0,1,2) and h in ("L0","L1","L2","L3")
    out.append({"id": i, "codability": c, "judgment": j, "coordination": co,
                "accountability": a, "embodied": e, "hierarchy": h, "module": m})

assert len(out) == len(rows), (len(out), len(rows))

os.makedirs(os.path.dirname(DST), exist_ok=True)
with open(DST, "w", encoding="utf-8", newline="") as f:
    json.dump(out, f, ensure_ascii=False)

# verify
with open(DST, "rb") as f:
    raw = f.read()
assert not raw.startswith(b"\xef\xbb\xbf"), "BOM found"
parsed = json.loads(raw.decode("utf-8"))
assert isinstance(parsed, list) and len(parsed) == len(rows)
for o in parsed:
    assert set(o.keys()) == {"id","codability","judgment","coordination","accountability","embodied","hierarchy","module"}, o
print("OK", len(parsed), "csv_rows", len(rows))
