# -*- coding: utf-8 -*-
import csv, json, os

src = r"D:\harness office\research\jobtask-agent\out\anno_input\2019\batch_074.csv"
dst = r"D:\harness office\research\jobtask-agent\out\anno_output\2019\batch_074.json"

rows = []
with open(src, "r", encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        rows.append((int(r["id"]), r["text"]))

# id -> (codability, judgment, coordination, accountability, embodied, hierarchy, module)
A = {
18168: (1,1,1,0,1,"L2","工艺工程"),
19606: (1,1,1,0,1,"L2","工艺工程"),
17011: (0,1,1,1,1,"L2","综合管理"),
14556: (1,0,0,0,1,"L0","EHS安全"),
21732: (1,1,1,0,0,"L1","IT数据"),
8074:  (0,0,0,0,1,"L0","客户服务"),
19915: (1,1,0,1,1,"L1","生产执行"),
18493: (0,1,1,0,1,"L1","行政法务"),
17548: (0,1,0,0,1,"L1","行政法务"),
9011:  (1,1,0,0,0,"L2","工艺工程"),
17945: (1,1,0,1,1,"L1","设备维护"),
9619:  (0,0,1,0,1,"L0","行政法务"),
22015: (1,1,0,1,1,"L1","设备维护"),
7321:  (1,1,1,1,0,"L2","财务会计"),
9682:  (0,1,1,0,1,"L2","销售"),
1867:  (0,1,1,1,1,"L2","客户服务"),
18838: (1,1,1,1,0,"L3","综合管理"),
14416: (0,0,0,0,1,"L0","生产执行"),
14648: (1,0,0,1,1,"L1","质量检验"),
12952: (2,0,0,0,0,"L0","IT数据"),
5464:  (1,1,1,0,0,"L2","研发技术"),
6564:  (0,0,0,0,1,"L0","综合管理"),
23076: (1,0,0,0,1,"L0","客户服务"),
16326: (0,1,1,0,1,"L2","工艺工程"),
3197:  (1,0,0,1,1,"L0","行政法务"),
102:   (1,1,1,0,1,"L2","人力资源"),
21518: (1,1,0,1,0,"L1","财务会计"),
16783: (0,1,1,0,1,"L1","研发技术"),
1847:  (0,0,1,0,1,"L0","客户服务"),
21512: (1,0,0,1,1,"L1","财务会计"),
21815: (0,1,1,0,0,"L2","IT数据"),
21463: (0,1,1,0,1,"L2","综合管理"),
21948: (1,1,0,1,1,"L1","工艺工程"),
21347: (1,1,1,1,1,"L2","物流仓储"),
977:   (0,1,1,1,1,"L2","人力资源"),
990:   (0,1,1,1,0,"L2","人力资源"),
12712: (0,0,0,0,1,"L0","生产执行"),
18049: (1,1,1,1,0,"L2","行政法务"),
13162: (1,0,0,1,0,"L0","财务会计"),
16308: (1,1,1,0,0,"L2","研发技术"),
12599: (1,1,0,1,1,"L1","生产执行"),
11372: (1,1,1,1,1,"L1","采购供应链"),
2487:  (2,0,0,0,0,"L0","财务会计"),
1546:  (1,1,0,0,1,"L1","研发技术"),
19912: (0,1,1,1,1,"L2","EHS安全"),
11865: (0,1,0,1,1,"L1","质量检验"),
11063: (0,1,1,1,1,"L2","EHS安全"),
130:   (1,1,1,0,1,"L2","研发技术"),
}

out = []
for i, t in rows:
    c, j, co, ac, em, h, m = A[i]
    out.append({"id": i, "codability": c, "judgment": j, "coordination": co,
                "accountability": ac, "embodied": em, "hierarchy": h, "module": m})

assert len(out) == len(rows), (len(out), len(rows))
os.makedirs(os.path.dirname(dst), exist_ok=True)
with open(dst, "w", encoding="utf-8", newline="") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

# verify
with open(dst, "rb") as f:
    raw = f.read()
assert not raw.startswith(b"\xef\xbb\xbf"), "BOM present"
data = json.loads(raw.decode("utf-8"))
keys = {"id","codability","judgment","coordination","accountability","embodied","hierarchy","module"}
assert isinstance(data, list)
assert len(data) == len(rows), (len(data), len(rows))
for d in data:
    assert set(d.keys()) == keys, d
print("OK rows=%d json=%d" % (len(rows), len(data)))
