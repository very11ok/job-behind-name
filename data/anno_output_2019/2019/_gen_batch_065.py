# -*- coding: utf-8 -*-
import json, os

rows = [
 (22282,0,1,1,1,1,"L2","生产执行"),
 (2922,1,1,1,1,1,"L1","EHS安全"),
 (992,1,1,1,0,0,"L2","人力资源"),
 (33,0,1,1,1,0,"L3","生产执行"),
 (20448,1,1,0,1,1,"L1","质量检验"),
 (7638,1,1,1,0,1,"L1","采购供应链"),
 (7064,0,0,0,0,1,"L0","生产执行"),
 (8949,1,1,1,0,0,"L2","物流仓储"),
 (16272,1,0,1,1,0,"L1","行政法务"),
 (673,2,0,0,0,0,"L1","财务会计"),
 (14012,2,0,0,0,0,"L0","生产执行"),
 (22016,1,1,0,0,0,"L1","研发技术"),
 (16205,1,1,0,0,0,"L1","研发技术"),
 (9254,0,1,1,0,1,"L1","客户服务"),
 (23850,2,0,0,0,0,"L0","物流仓储"),
 (21409,0,1,1,0,1,"L1","客户服务"),
 (9389,1,1,0,0,0,"L1","研发技术"),
 (2392,1,1,1,0,0,"L1","设备维护"),
 (12050,0,0,0,0,1,"L0","生产执行"),
 (20753,0,1,0,0,1,"L0","其他"),
 (11625,0,1,1,0,1,"L1","设备维护"),
 (20727,1,1,1,0,1,"L1","客户服务"),
 (3973,1,1,1,0,0,"L1","研发技术"),
 (22904,2,0,0,0,0,"L1","IT数据"),
 (6579,2,0,0,1,0,"L0","行政法务"),
 (408,2,0,1,0,0,"L0","其他"),
 (22037,1,1,1,1,1,"L2","生产执行"),
 (5199,0,1,1,1,0,"L3","综合管理"),
 (13019,0,1,0,0,0,"L2","工艺工程"),
 (11384,1,0,1,0,0,"L1","采购供应链"),
 (4410,0,1,1,1,1,"L1","EHS安全"),
 (1940,1,1,0,1,1,"L1","物流仓储"),
 (20306,1,1,0,1,1,"L1","生产执行"),
 (16190,1,1,0,0,0,"L1","市场"),
 (8495,1,1,0,1,1,"L1","质量检验"),
 (15375,0,1,1,0,0,"L2","市场"),
 (10158,0,1,0,1,1,"L1","生产执行"),
 (21342,0,1,1,1,1,"L2","设备维护"),
 (21381,0,1,1,0,0,"L2","综合管理"),
 (15473,1,1,1,1,0,"L2","财务会计"),
 (12790,0,1,1,1,1,"L1","生产执行"),
 (22744,1,1,0,1,1,"L1","质量检验"),
 (15789,0,1,1,1,1,"L2","行政法务"),
 (8208,1,1,0,0,1,"L1","物流仓储"),
 (9731,1,1,1,0,0,"L2","物流仓储"),
 (16066,2,0,1,0,0,"L0","采购供应链"),
 (18024,1,1,1,1,0,"L2","行政法务"),
 (16587,1,1,1,0,0,"L1","研发技术"),
]

out = []
for (i, c, j, co, a, e, h, m) in rows:
    out.append({"id": i, "codability": c, "judgment": j, "coordination": co,
                "accountability": a, "embodied": e, "hierarchy": h, "module": m})

path = r"D:\harness office\research\jobtask-agent\out\anno_output\2019\batch_065.json"
os.makedirs(os.path.dirname(path), exist_ok=True)

lines = ["["]
for k, rec in enumerate(out):
    s = "  " + json.dumps(rec, ensure_ascii=False)
    if k < len(out) - 1:
        s += ","
    lines.append(s)
lines.append("]")
text = "\n".join(lines) + "\n"

with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write(text)

# verify
with open(path, "rb") as f:
    raw = f.read()
assert not raw.startswith(b"\xef\xbb\xbf"), "BOM detected"
data = json.loads(raw.decode("utf-8"))
assert isinstance(data, list)
assert len(data) == len(rows) == 48
keys = {"id","codability","judgment","coordination","accountability","embodied","hierarchy","module"}
for rec in data:
    assert set(rec.keys()) == keys, rec
print("OK", len(data))
