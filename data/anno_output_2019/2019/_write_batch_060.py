import json, io

data = [
{"id":19526,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L3","module":"EHS安全"},
{"id":7557,"codability":1,"judgment":1,"coordination":1,"accountability":0,"embodied":0,"hierarchy":"L2","module":"市场"},
{"id":19638,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L2","module":"研发技术"},
{"id":19047,"codability":1,"judgment":1,"coordination":0,"accountability":1,"embodied":0,"hierarchy":"L2","module":"行政法务"},
{"id":9366,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L1","module":"其他"},
{"id":22029,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L2","module":"工艺工程"},
{"id":12309,"codability":2,"judgment":0,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L0","module":"生产执行"},
{"id":1549,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L1","module":"质量检验"},
{"id":9991,"codability":1,"judgment":0,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L0","module":"设备维护"},
{"id":14479,"codability":1,"judgment":0,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L0","module":"物流仓储"},
{"id":3354,"codability":1,"judgment":1,"coordination":1,"accountability":0,"embodied":0,"hierarchy":"L2","module":"人力资源"},
{"id":15675,"codability":1,"judgment":1,"coordination":0,"accountability":1,"embodied":0,"hierarchy":"L3","module":"财务会计"},
{"id":17562,"codability":0,"judgment":1,"coordination":1,"accountability":0,"embodied":0,"hierarchy":"L2","module":"行政法务"},
{"id":1356,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L1","module":"研发技术"},
{"id":11154,"codability":1,"judgment":0,"coordination":1,"accountability":0,"embodied":1,"hierarchy":"L0","module":"客户服务"},
{"id":2055,"codability":1,"judgment":0,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L0","module":"生产执行"},
{"id":15819,"codability":0,"judgment":1,"coordination":1,"accountability":0,"embodied":0,"hierarchy":"L2","module":"综合管理"},
{"id":4219,"codability":1,"judgment":0,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L1","module":"生产执行"},
{"id":18574,"codability":1,"judgment":0,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L0","module":"行政法务"},
{"id":988,"codability":1,"judgment":1,"coordination":0,"accountability":1,"embodied":0,"hierarchy":"L2","module":"人力资源"},
{"id":15477,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L2","module":"生产执行"},
{"id":6476,"codability":1,"judgment":0,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L0","module":"客户服务"},
{"id":21221,"codability":1,"judgment":1,"coordination":1,"accountability":0,"embodied":0,"hierarchy":"L2","module":"市场"},
{"id":21860,"codability":0,"judgment":1,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L2","module":"EHS安全"},
{"id":22035,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L1","module":"生产执行"},
{"id":20628,"codability":1,"judgment":0,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L0","module":"行政法务"},
{"id":3679,"codability":0,"judgment":1,"coordination":1,"accountability":1,"embodied":0,"hierarchy":"L2","module":"研发技术"},
{"id":12701,"codability":1,"judgment":0,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L0","module":"设备维护"},
{"id":15563,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L2","module":"工艺工程"},
{"id":15797,"codability":0,"judgment":1,"coordination":1,"accountability":0,"embodied":0,"hierarchy":"L2","module":"行政法务"},
{"id":22814,"codability":1,"judgment":0,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L0","module":"IT数据"},
{"id":23261,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L1","module":"市场"},
{"id":21869,"codability":1,"judgment":1,"coordination":1,"accountability":0,"embodied":0,"hierarchy":"L2","module":"EHS安全"},
{"id":22046,"codability":1,"judgment":0,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L0","module":"生产执行"},
{"id":21292,"codability":0,"judgment":1,"coordination":1,"accountability":1,"embodied":0,"hierarchy":"L2","module":"行政法务"},
{"id":21998,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L1","module":"设备维护"},
{"id":4052,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L1","module":"其他"},
{"id":15697,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L1","module":"采购供应链"},
{"id":2438,"codability":1,"judgment":0,"coordination":0,"accountability":1,"embodied":1,"hierarchy":"L1","module":"质量检验"},
{"id":9739,"codability":2,"judgment":0,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L0","module":"行政法务"},
{"id":16476,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L2","module":"IT数据"},
{"id":15652,"codability":2,"judgment":0,"coordination":1,"accountability":0,"embodied":0,"hierarchy":"L0","module":"行政法务"},
{"id":18659,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L1","module":"其他"},
{"id":1592,"codability":0,"judgment":1,"coordination":1,"accountability":0,"embodied":1,"hierarchy":"L2","module":"客户服务"},
{"id":21709,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L2","module":"IT数据"},
{"id":20213,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L2","module":"研发技术"},
{"id":22855,"codability":0,"judgment":0,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L0","module":"客户服务"},
{"id":21593,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L2","module":"财务会计"}
]

import csv, os
src = r"D:\harness office\research\jobtask-agent\out\anno_input\2019\batch_060.csv"
with open(src, newline='', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))
assert len(rows) == len(data), f"count mismatch: csv={len(rows)} json={len(data)}"
ids_csv = [int(r['id']) for r in rows]
ids_json = [d['id'] for d in data]
assert ids_csv == ids_json, "id order mismatch"

out = r"D:\harness office\research\jobtask-agent\out\anno_output\2019\batch_060.json"
os.makedirs(os.path.dirname(out), exist_ok=True)
with io.open(out, 'w', encoding='utf-8', newline='') as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
print("written", out, len(data))
