# -*- coding: utf-8 -*-
import csv, json, io, sys

rows = [
    (231,   1,1,1,0,0,"L2","综合管理"),
    (19225, 1,0,0,1,1,"L1","其他"),
    (9877,  1,1,0,0,0,"L1","财务会计"),
    (5170,  1,0,0,0,1,"L0","生产执行"),
    (23260, 1,1,0,1,0,"L2","财务会计"),
    (4023,  0,1,1,0,1,"L1","其他"),
    (3475,  1,1,0,0,0,"L2","IT数据"),
    (7492,  1,1,0,1,0,"L2","研发技术"),
    (7207,  1,1,1,0,0,"L2","IT数据"),
    (11221, 1,1,1,0,0,"L1","其他"),
    (21630, 1,1,1,0,0,"L2","IT数据"),
    (8204,  0,1,1,1,1,"L1","物流仓储"),
    (1213,  1,1,1,0,0,"L2","综合管理"),
    (22704, 0,1,0,1,1,"L2","其他"),
    (18188, 1,1,0,0,1,"L1","研发技术"),
    (15430, 1,1,0,1,0,"L1","质量检验"),
    (5328,  1,1,1,1,1,"L2","研发技术"),
    (4610,  1,1,1,1,0,"L2","综合管理"),
    (1524,  1,1,0,0,0,"L2","行政法务"),
    (4778,  1,0,0,0,1,"L0","生产执行"),
    (4329,  1,0,0,0,0,"L0","综合管理"),
    (14211, 1,0,0,0,1,"L0","生产执行"),
    (9672,  0,0,1,0,1,"L1","销售"),
    (5116,  2,0,1,0,1,"L0","客户服务"),
    (22666, 1,1,0,0,0,"L1","综合管理"),
    (20877, 1,1,0,1,0,"L2","行政法务"),
    (4581,  1,1,1,0,0,"L1","销售"),
    (17,    1,1,0,0,0,"L2","市场"),
    (9256,  1,1,0,0,1,"L1","生产执行"),
    (21612, 1,1,0,1,0,"L2","EHS安全"),
    (7237,  0,1,1,0,1,"L1","综合管理"),
    (22137, 0,0,1,0,0,"L2","综合管理"),
    (2190,  1,0,0,0,1,"L0","生产执行"),
    (8779,  1,0,0,0,1,"L0","生产执行"),
    (14743, 1,1,0,1,0,"L1","IT数据"),
    (3157,  2,0,0,0,0,"L0","销售"),
    (14758, 1,1,0,0,0,"L1","质量检验"),
    (2692,  1,0,1,0,0,"L0","人力资源"),
    (3737,  2,0,0,0,0,"L0","行政法务"),
    (769,   1,0,1,0,0,"L0","行政法务"),
    (23361, 1,1,1,0,0,"L1","生产执行"),
    (12693, 1,0,0,0,1,"L0","生产执行"),
    (20608, 2,0,0,0,0,"L0","销售"),
    (18595, 1,1,0,1,0,"L3","综合管理"),
    (18853, 1,1,0,1,0,"L1","人力资源"),
    (15729, 1,1,0,0,1,"L1","市场"),
    (9006,  1,1,1,1,1,"L1","质量检验"),
    (13302, 2,0,0,0,1,"L0","行政法务"),
]

data = [
    {
        "id": r[0], "codability": r[1], "judgment": r[2],
        "coordination": r[3], "accountability": r[4], "embodied": r[5],
        "hierarchy": r[6], "module": r[7],
    }
    for r in rows
]

out_path = r"D:\harness office\research\jobtask-agent\out\anno_output\2019\batch_037.json"
csv_path = r"D:\harness office\research\jobtask-agent\out\anno_input\2019\batch_037.csv"

with io.open(out_path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

# verify
with io.open(out_path, "r", encoding="utf-8") as f:
    parsed = json.load(f)
with io.open(csv_path, "r", encoding="utf-8-sig") as f:
    csv_ids = [int(r["id"]) for r in csv.DictReader(f)]

fields = ["id","codability","judgment","coordination","accountability","embodied","hierarchy","module"]
ok_fields = all(all(k in d for k in fields) for d in parsed)
ids_match = [d["id"] for d in parsed] == csv_ids
levels = all(d["hierarchy"] in ("L0","L1","L2","L3") for d in parsed)
mods = {"生产执行","质量检验","研发技术","工艺工程","设备维护","销售","市场","采购供应链","物流仓储","人力资源","财务会计","行政法务","IT数据","EHS安全","客户服务","综合管理","其他"}
mods_ok = all(d["module"] in mods for d in parsed)
bits_ok = all(d[k] in (0,1,2) if k=="codability" else d[k] in (0,1) for d in parsed for k in ["codability","judgment","coordination","accountability","embodied"])

print("jsonCount=%d csvCount=%d idsMatch=%s fieldsOk=%s levelsOk=%s modsOk=%s bitsOk=%s"
      % (len(parsed), len(csv_ids), ids_match, ok_fields, levels, mods_ok, bits_ok))
if not (len(parsed) == len(csv_ids) and ids_match and ok_fields and levels and mods_ok and bits_ok):
    sys.exit(1)
