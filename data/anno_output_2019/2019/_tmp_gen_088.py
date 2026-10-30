# -*- coding: utf-8 -*-
import json, csv, os, sys

SRC = r"D:\harness office\research\jobtask-agent\out\anno_input\2019\batch_088.csv"
DST = r"D:\harness office\research\jobtask-agent\out\anno_output\2019\batch_088.json"

with open(SRC, "r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))
ids = [int(r["id"]) for r in rows]
assert len(ids) == 48, len(ids)

A = {
 2414:  (2,0,0,0,0,"L0","财务会计"),
 1731:  (1,1,0,0,1,"L1","市场"),
 23009: (1,1,1,0,1,"L2","EHS安全"),
 17668: (0,1,1,0,1,"L2","客户服务"),
 17215: (1,1,1,0,1,"L1","其他"),
 9579:  (1,0,1,0,1,"L0","行政法务"),
 949:   (1,1,0,0,0,"L1","市场"),
 20267: (1,0,0,0,0,"L1","销售"),
 18075: (1,1,0,0,0,"L1","其他"),
 18865: (1,1,1,0,0,"L1","人力资源"),
 21665: (0,1,1,0,0,"L2","IT数据"),
 5440:  (1,1,1,0,1,"L2","市场"),
 10029: (1,0,0,0,1,"L0","生产执行"),
 20712: (1,1,1,1,0,"L1","采购供应链"),
 8480:  (1,1,0,0,1,"L1","设备维护"),
 7974:  (2,0,0,0,0,"L0","其他"),
 3698:  (2,0,0,0,0,"L0","行政法务"),
 21144: (1,1,1,0,1,"L1","EHS安全"),
 2408:  (1,1,1,0,1,"L1","客户服务"),
 20977: (1,1,1,0,0,"L2","研发技术"),
 20859: (1,0,0,0,1,"L0","其他"),
 17687: (2,0,0,0,0,"L0","物流仓储"),
 2388:  (2,0,0,0,0,"L0","行政法务"),
 14008: (1,1,0,0,1,"L1","生产执行"),
 1285:  (1,1,0,1,0,"L1","IT数据"),
 15345: (1,0,1,0,1,"L0","EHS安全"),
 438:   (1,0,0,0,1,"L0","其他"),
 23212: (1,1,1,0,0,"L1","财务会计"),
 13509: (1,0,0,0,1,"L0","生产执行"),
 3723:  (1,1,1,0,1,"L1","市场"),
 3001:  (1,1,0,0,1,"L1","设备维护"),
 21520: (1,1,1,1,0,"L2","财务会计"),
 23644: (1,1,0,0,1,"L1","工艺工程"),
 574:   (1,1,1,1,0,"L2","综合管理"),
 950:   (0,1,1,1,0,"L3","市场"),
 3114:  (1,1,1,0,0,"L2","工艺工程"),
 12331: (1,1,0,0,1,"L1","设备维护"),
 12460: (1,0,0,0,1,"L0","生产执行"),
 21270: (0,1,1,0,1,"L2","综合管理"),
 21597: (1,1,0,1,0,"L1","财务会计"),
 8364:  (1,0,0,0,1,"L0","设备维护"),
 1018:  (1,1,1,0,0,"L2","人力资源"),
 14692: (1,1,0,0,0,"L1","IT数据"),
 23099: (1,1,1,0,1,"L1","客户服务"),
 21486: (1,1,1,1,0,"L2","EHS安全"),
 21915: (1,1,0,0,0,"L2","研发技术"),
 4611:  (1,1,1,1,0,"L2","销售"),
 23367: (1,1,1,0,1,"L1","设备维护"),
}

MODULES = {"生产执行","质量检验","研发技术","工艺工程","设备维护","销售","市场","采购供应链","物流仓储","人力资源","财务会计","行政法务","IT数据","EHS安全","客户服务","综合管理","其他"}

out = []
for i in ids:
    cod, j, co, ac, em, hi, mod = A[i]
    assert cod in (0,1,2), i
    assert j in (0,1) and co in (0,1) and ac in (0,1) and em in (0,1), i
    assert hi in ("L0","L1","L2","L3"), i
    assert mod in MODULES, i
    out.append({"id": i, "codability": cod, "judgment": j, "coordination": co,
                "accountability": ac, "embodied": em, "hierarchy": hi, "module": mod})

os.makedirs(os.path.dirname(DST), exist_ok=True)
with open(DST, "w", encoding="utf-8", newline="") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
    f.write("\n")

# verify
with open(DST, "rb") as f:
    raw = f.read()
assert not raw.startswith(b"\xef\xbb\xbf"), "BOM present"
data = json.loads(raw.decode("utf-8"))
assert isinstance(data, list), "top level not list"
assert len(data) == len(ids), (len(data), len(ids))
keys = {"id","codability","judgment","coordination","accountability","embodied","hierarchy","module"}
for rec in data:
    assert set(rec.keys()) == keys, rec
    assert isinstance(rec["id"], int)
print("OK rows=%d bytes=%d bom=%s" % (len(data), len(raw), raw[:3] == b"\xef\xbb\xbf"))
