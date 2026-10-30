# -*- coding: utf-8 -*-
import json, csv, sys

csv_path = r"D:\harness office\research\jobtask-agent\out\anno_input\2019\batch_021.csv"
out_path = r"D:\harness office\research\jobtask-agent\out\anno_output\2019\batch_021.json"

# (id, codability, judgment, coordination, accountability, embodied, hierarchy, module)
ann = [
    (23144, 0, 1, 1, 0, 1, "L1", "生产执行"),   # Monitor stations/games, move dealers for staffing
    (21528, 0, 1, 1, 1, 0, "L2", "财务会计"),   # Represent clients before taxing authorities
    (18630, 1, 0, 1, 0, 1, "L1", "人力资源"),   # Attend meetings/conferences/training workshops, serve on committees
    (21733, 1, 1, 0, 0, 0, "L2", "IT数据"),     # Design, program, model GIS applications
    (15859, 1, 1, 0, 0, 0, "L2", "EHS安全"),    # Feasibility/cost-benefit studies for environmental remediation
    (23936, 1, 1, 0, 1, 1, "L1", "设备维护"),   # Test and repair track circuits
    (18066, 1, 1, 0, 0, 0, "L1", "综合管理"),   # Write or update SOPs, work instructions, policies
    (1019,  1, 1, 0, 0, 0, "L1", "人力资源"),   # Prepare training budget for department
    (9,     0, 1, 1, 1, 0, "L2", "财务会计"),   # Prepare budgets and approve budget expenditures
    (1704,  1, 0, 0, 0, 1, "L0", "客户服务"),   # Issue identification cards to borrowers
    (16792, 1, 1, 1, 0, 0, "L2", "研发技术"),   # Communicate research results via conferences/publications
    (19984, 1, 1, 0, 0, 0, "L2", "EHS安全"),    # Develop programs/policy recommendations for environmental goals
    (20908, 2, 1, 0, 0, 0, "L1", "行政法务"),   # Archive documents, conduct research, read copy
    (10896, 1, 1, 0, 1, 1, "L1", "质量检验"),   # Inspect parts for surface defects
    (18180, 1, 1, 0, 1, 0, "L2", "工艺工程"),   # Review product designs for manufacturability/completeness
    (18159, 1, 1, 0, 0, 0, "L2", "研发技术"),   # Analyze/interpret energy data with engineering software
    (20751, 0, 1, 1, 1, 1, "L1", "物流仓储"),   # Deliver arrangements or oversee delivery employees
    (14751, 1, 1, 0, 0, 0, "L2", "IT数据"),     # Recommend Web site improvements, develop budgets
    (15899, 2, 0, 0, 0, 0, "L0", "物流仓储"),   # Maintain logistics records per corporate policies
    (20822, 1, 1, 1, 0, 0, "L1", "销售"),       # Draw up specifications and discuss projects with customers
    (16718, 1, 0, 0, 0, 1, "L0", "生产执行"),   # Mix, pour, or use processing chemicals per standards
    (8403,  0, 0, 0, 0, 1, "L0", "生产执行"),   # Operate lifts, winches to move heavy curtain doors
    (11768, 1, 1, 1, 0, 0, "L2", "EHS安全"),    # Consult with clients to assess risks, determine security requirements
    (16365, 1, 1, 0, 0, 0, "L2", "工艺工程"),   # Develop process flows/work instructions/SOPs for RFID systems
    (16433, 1, 1, 1, 1, 0, "L2", "研发技术"),   # Conduct automotive design reviews
    (22027, 1, 1, 1, 0, 1, "L2", "设备维护"),   # Coordinate equipment purchases, installations, transfers
    (21467, 1, 1, 0, 0, 0, "L2", "综合管理"),   # Identify project needs by reviewing objectives and schedules
    (17660, 1, 1, 0, 0, 0, "L3", "市场"),       # Develop marketing or strategic plans for sales territories
    (22083, 1, 1, 0, 0, 0, "L1", "设备维护"),   # Prepare inspection/reliability schedules, work plans
    (2385,  0, 0, 1, 0, 1, "L0", "客户服务"),   # Greet new arrivals, introduce, explain rules, encourage participation
    (12007, 0, 1, 0, 0, 1, "L1", "生产执行"),   # Pour and regulate molten metal into molds
    (14293, 1, 1, 1, 0, 1, "L1", "生产执行"),   # Collaborate with other operators to solve unit problems
    (21610, 1, 1, 1, 0, 0, "L2", "综合管理"),   # Contribute to development of risk management systems
    (16481, 1, 1, 0, 0, 0, "L2", "研发技术"),   # Design mechatronics components
    (21753, 1, 1, 1, 0, 0, "L2", "IT数据"),     # Discuss security solutions with IT teams or management
    (11302, 2, 0, 0, 0, 0, "L0", "财务会计"),   # File and maintain loan records
    (8986,  0, 1, 0, 1, 1, "L2", "EHS安全"),    # Determine causes of fires and prevention ways
    (17518, 1, 1, 1, 0, 1, "L2", "客户服务"),   # Prepare/provide genetics-related educational materials
    (16426, 1, 1, 0, 0, 0, "L2", "研发技术"),   # Conduct research studies in automotive engineering
    (16435, 1, 1, 0, 0, 0, "L2", "研发技术"),   # Build models for algorithm/control verification testing
    (11742, 1, 1, 0, 1, 1, "L1", "设备维护"),   # Construct, test, maintain, repair substation relays
    (2672,  2, 0, 0, 0, 0, "L0", "客户服务"),   # Verify customer and order information for correctness
    (18472, 1, 1, 0, 1, 1, "L2", "工艺工程"),   # Evaluate chemical equipment/processes for compliance
    (3318,  0, 1, 0, 1, 1, "L1", "EHS安全"),    # Inspect/review projects for code compliance
    (21507, 1, 1, 0, 1, 0, "L2", "财务会计"),   # Collect/analyze data to detect fraud, non-compliance
    (6990,  0, 1, 1, 1, 1, "L1", "综合管理"),   # Supervise housekeeping personnel
    (22088, 1, 1, 0, 0, 0, "L1", "质量检验"),   # Analyze test data to identify defects/calibration
    (1122,  0, 1, 1, 1, 1, "L2", "综合管理"),   # Organize and coordinate staff for meetings at facility
]

with open(csv_path, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))
csv_ids = [int(r["id"]) for r in rows]
ann_ids = [a[0] for a in ann]
assert len(csv_ids) == len(ann_ids) == 48, (len(csv_ids), len(ann_ids))
assert sorted(csv_ids) == sorted(ann_ids), "id mismatch"

records = [
    {"id": i, "codability": c, "judgment": j, "coordination": co,
     "accountability": a, "embodied": e, "hierarchy": h, "module": m}
    for (i, c, j, co, a, e, h, m) in ann
]
# order to match CSV row order
order = {i: k for k, i in enumerate(csv_ids)}
records.sort(key=lambda r: order[r["id"]])

with open(out_path, "w", encoding="utf-8", newline="") as f:
    json.dump(records, f, ensure_ascii=False, indent=1)
print("written", len(records), "->", out_path)
