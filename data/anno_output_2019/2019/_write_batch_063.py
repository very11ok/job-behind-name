import csv, json, io, os

csv_path = r"D:\harness office\research\jobtask-agent\out\anno_input\2019\batch_063.csv"
out_path = r"D:\harness office\research\jobtask-agent\out\anno_output\2019\batch_063.json"

with io.open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))
ids = [int(r["id"]) for r in rows]

data = [
    {"id": 23175, "codability": 1, "judgment": 1, "coordination": 1, "accountability": 1, "embodied": 1, "hierarchy": "L1", "module": "人力资源"},
    {"id": 17612, "codability": 1, "judgment": 1, "coordination": 1, "accountability": 0, "embodied": 1, "hierarchy": "L1", "module": "客户服务"},
    {"id": 22, "codability": 1, "judgment": 1, "coordination": 1, "accountability": 1, "embodied": 0, "hierarchy": "L2", "module": "综合管理"},
    {"id": 17763, "codability": 1, "judgment": 0, "coordination": 0, "accountability": 0, "embodied": 0, "hierarchy": "L0", "module": "IT数据"},
    {"id": 9217, "codability": 1, "judgment": 1, "coordination": 1, "accountability": 1, "embodied": 1, "hierarchy": "L2", "module": "EHS安全"},
    {"id": 7736, "codability": 1, "judgment": 0, "coordination": 0, "accountability": 1, "embodied": 0, "hierarchy": "L0", "module": "其他"},
    {"id": 5693, "codability": 0, "judgment": 1, "coordination": 1, "accountability": 1, "embodied": 1, "hierarchy": "L1", "module": "其他"},
    {"id": 1535, "codability": 1, "judgment": 1, "coordination": 0, "accountability": 1, "embodied": 1, "hierarchy": "L1", "module": "质量检验"},
    {"id": 21070, "codability": 0, "judgment": 0, "coordination": 1, "accountability": 0, "embodied": 1, "hierarchy": "L0", "module": "其他"},
    {"id": 9544, "codability": 1, "judgment": 1, "coordination": 1, "accountability": 0, "embodied": 1, "hierarchy": "L0", "module": "设备维护"},
    {"id": 12773, "codability": 1, "judgment": 1, "coordination": 1, "accountability": 0, "embodied": 1, "hierarchy": "L1", "module": "客户服务"},
    {"id": 21235, "codability": 0, "judgment": 1, "coordination": 1, "accountability": 0, "embodied": 1, "hierarchy": "L2", "module": "客户服务"},
    {"id": 1301, "codability": 1, "judgment": 1, "coordination": 1, "accountability": 1, "embodied": 0, "hierarchy": "L2", "module": "IT数据"},
    {"id": 14657, "codability": 0, "judgment": 1, "coordination": 1, "accountability": 1, "embodied": 1, "hierarchy": "L2", "module": "客户服务"},
    {"id": 18530, "codability": 0, "judgment": 1, "coordination": 1, "accountability": 1, "embodied": 1, "hierarchy": "L2", "module": "其他"},
    {"id": 21315, "codability": 1, "judgment": 1, "coordination": 0, "accountability": 1, "embodied": 0, "hierarchy": "L1", "module": "财务会计"},
    {"id": 9736, "codability": 1, "judgment": 1, "coordination": 0, "accountability": 1, "embodied": 0, "hierarchy": "L1", "module": "财务会计"},
    {"id": 287, "codability": 0, "judgment": 1, "coordination": 1, "accountability": 0, "embodied": 0, "hierarchy": "L2", "module": "市场"},
    {"id": 21298, "codability": 0, "judgment": 1, "coordination": 1, "accountability": 1, "embodied": 0, "hierarchy": "L2", "module": "IT数据"},
    {"id": 23675, "codability": 1, "judgment": 0, "coordination": 0, "accountability": 0, "embodied": 1, "hierarchy": "L0", "module": "生产执行"},
    {"id": 19650, "codability": 1, "judgment": 1, "coordination": 1, "accountability": 0, "embodied": 0, "hierarchy": "L2", "module": "研发技术"},
    {"id": 11249, "codability": 1, "judgment": 0, "coordination": 1, "accountability": 0, "embodied": 0, "hierarchy": "L0", "module": "客户服务"},
    {"id": 16165, "codability": 1, "judgment": 1, "coordination": 1, "accountability": 1, "embodied": 0, "hierarchy": "L2", "module": "人力资源"},
    {"id": 21551, "codability": 1, "judgment": 1, "coordination": 0, "accountability": 1, "embodied": 1, "hierarchy": "L1", "module": "财务会计"},
    {"id": 9792, "codability": 2, "judgment": 0, "coordination": 0, "accountability": 1, "embodied": 0, "hierarchy": "L0", "module": "其他"},
    {"id": 16286, "codability": 1, "judgment": 1, "coordination": 1, "accountability": 0, "embodied": 0, "hierarchy": "L1", "module": "IT数据"},
    {"id": 8826, "codability": 0, "judgment": 1, "coordination": 1, "accountability": 1, "embodied": 0, "hierarchy": "L3", "module": "综合管理"},
    {"id": 19673, "codability": 0, "judgment": 1, "coordination": 0, "accountability": 1, "embodied": 0, "hierarchy": "L2", "module": "研发技术"},
    {"id": 10365, "codability": 0, "judgment": 0, "coordination": 0, "accountability": 0, "embodied": 1, "hierarchy": "L0", "module": "生产执行"},
    {"id": 14153, "codability": 1, "judgment": 1, "coordination": 0, "accountability": 0, "embodied": 1, "hierarchy": "L0", "module": "生产执行"},
    {"id": 14260, "codability": 1, "judgment": 0, "coordination": 0, "accountability": 0, "embodied": 1, "hierarchy": "L0", "module": "生产执行"},
    {"id": 9667, "codability": 0, "judgment": 0, "coordination": 1, "accountability": 0, "embodied": 0, "hierarchy": "L1", "module": "综合管理"},
    {"id": 14212, "codability": 2, "judgment": 0, "coordination": 0, "accountability": 0, "embodied": 0, "hierarchy": "L0", "module": "设备维护"},
    {"id": 7856, "codability": 1, "judgment": 1, "coordination": 1, "accountability": 1, "embodied": 0, "hierarchy": "L1", "module": "行政法务"},
    {"id": 12426, "codability": 1, "judgment": 1, "coordination": 0, "accountability": 0, "embodied": 1, "hierarchy": "L0", "module": "生产执行"},
    {"id": 570, "codability": 0, "judgment": 1, "coordination": 1, "accountability": 1, "embodied": 0, "hierarchy": "L2", "module": "人力资源"},
    {"id": 9517, "codability": 1, "judgment": 1, "coordination": 1, "accountability": 1, "embodied": 0, "hierarchy": "L2", "module": "综合管理"},
    {"id": 20367, "codability": 0, "judgment": 1, "coordination": 1, "accountability": 0, "embodied": 0, "hierarchy": "L1", "module": "行政法务"},
    {"id": 20396, "codability": 1, "judgment": 1, "coordination": 0, "accountability": 1, "embodied": 1, "hierarchy": "L1", "module": "设备维护"},
    {"id": 140, "codability": 1, "judgment": 1, "coordination": 0, "accountability": 0, "embodied": 0, "hierarchy": "L1", "module": "研发技术"},
    {"id": 14840, "codability": 0, "judgment": 1, "coordination": 1, "accountability": 1, "embodied": 0, "hierarchy": "L1", "module": "人力资源"},
    {"id": 20271, "codability": 2, "judgment": 0, "coordination": 0, "accountability": 0, "embodied": 0, "hierarchy": "L0", "module": "物流仓储"},
    {"id": 9793, "codability": 0, "judgment": 1, "coordination": 1, "accountability": 1, "embodied": 0, "hierarchy": "L1", "module": "其他"},
    {"id": 2781, "codability": 1, "judgment": 0, "coordination": 1, "accountability": 0, "embodied": 0, "hierarchy": "L0", "module": "行政法务"},
    {"id": 5067, "codability": 1, "judgment": 1, "coordination": 1, "accountability": 0, "embodied": 1, "hierarchy": "L1", "module": "生产执行"},
    {"id": 16164, "codability": 1, "judgment": 1, "coordination": 1, "accountability": 1, "embodied": 0, "hierarchy": "L2", "module": "综合管理"},
    {"id": 16163, "codability": 0, "judgment": 1, "coordination": 1, "accountability": 1, "embodied": 0, "hierarchy": "L2", "module": "综合管理"},
    {"id": 21970, "codability": 1, "judgment": 0, "coordination": 0, "accountability": 0, "embodied": 1, "hierarchy": "L0", "module": "生产执行"},
]

assert [d["id"] for d in data] == ids, (len(data), len(ids))
assert len(data) == len(rows)

os.makedirs(os.path.dirname(out_path), exist_ok=True)
with io.open(out_path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
    f.write("\n")

print("rows", len(rows), "written", len(data))
