# -*- coding: utf-8 -*-
import json, os, csv

annos = [
 {"id":16482,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L2","module":"研发技术"},
 {"id":21483,"codability":1,"judgment":1,"coordination":1,"accountability":0,"embodied":0,"hierarchy":"L2","module":"综合管理"},
 {"id":781,"codability":2,"judgment":0,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L0","module":"行政法务"},
 {"id":21312,"codability":0,"judgment":1,"coordination":1,"accountability":1,"embodied":0,"hierarchy":"L2","module":"综合管理"},
 {"id":21499,"codability":1,"judgment":1,"coordination":1,"accountability":0,"embodied":0,"hierarchy":"L2","module":"IT数据"},
 {"id":11959,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L1","module":"工艺工程"},
 {"id":2716,"codability":1,"judgment":0,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L0","module":"人力资源"},
 {"id":11758,"codability":0,"judgment":1,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L1","module":"设备维护"},
 {"id":16238,"codability":1,"judgment":1,"coordination":1,"accountability":0,"embodied":0,"hierarchy":"L1","module":"IT数据"},
 {"id":21385,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L1","module":"研发技术"},
 {"id":23935,"codability":1,"judgment":1,"coordination":1,"accountability":0,"embodied":0,"hierarchy":"L2","module":"综合管理"},
 {"id":16147,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L2","module":"市场"},
 {"id":20776,"codability":1,"judgment":1,"coordination":1,"accountability":0,"embodied":0,"hierarchy":"L1","module":"客户服务"},
 {"id":8951,"codability":1,"judgment":1,"coordination":1,"accountability":1,"embodied":0,"hierarchy":"L2","module":"采购供应链"},
 {"id":14543,"codability":0,"judgment":0,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L0","module":"设备维护"},
 {"id":10880,"codability":0,"judgment":0,"coordination":1,"accountability":0,"embodied":1,"hierarchy":"L1","module":"人力资源"},
 {"id":7394,"codability":0,"judgment":1,"coordination":0,"accountability":1,"embodied":1,"hierarchy":"L1","module":"设备维护"},
 {"id":22675,"codability":0,"judgment":0,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L0","module":"其他"},
 {"id":16048,"codability":0,"judgment":1,"coordination":1,"accountability":1,"embodied":0,"hierarchy":"L2","module":"行政法务"},
 {"id":2324,"codability":0,"judgment":0,"coordination":1,"accountability":0,"embodied":1,"hierarchy":"L0","module":"客户服务"},
 {"id":15626,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L1","module":"EHS安全"},
 {"id":2695,"codability":0,"judgment":1,"coordination":1,"accountability":0,"embodied":1,"hierarchy":"L1","module":"人力资源"},
 {"id":12970,"codability":1,"judgment":1,"coordination":1,"accountability":0,"embodied":0,"hierarchy":"L2","module":"综合管理"},
 {"id":20871,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L1","module":"质量检验"},
 {"id":1297,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L2","module":"IT数据"},
 {"id":18650,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L1","module":"设备维护"},
 {"id":7683,"codability":0,"judgment":1,"coordination":1,"accountability":0,"embodied":1,"hierarchy":"L1","module":"其他"},
 {"id":9336,"codability":1,"judgment":1,"coordination":1,"accountability":1,"embodied":0,"hierarchy":"L1","module":"其他"},
 {"id":8203,"codability":1,"judgment":1,"coordination":1,"accountability":0,"embodied":0,"hierarchy":"L1","module":"物流仓储"},
 {"id":19042,"codability":0,"judgment":1,"coordination":1,"accountability":1,"embodied":1,"hierarchy":"L1","module":"EHS安全"},
 {"id":7241,"codability":0,"judgment":1,"coordination":1,"accountability":1,"embodied":1,"hierarchy":"L2","module":"综合管理"},
 {"id":11908,"codability":2,"judgment":0,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L0","module":"生产执行"},
 {"id":16961,"codability":0,"judgment":1,"coordination":0,"accountability":1,"embodied":1,"hierarchy":"L1","module":"EHS安全"},
 {"id":2997,"codability":0,"judgment":1,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L1","module":"设备维护"},
 {"id":7537,"codability":1,"judgment":1,"coordination":1,"accountability":0,"embodied":0,"hierarchy":"L2","module":"综合管理"},
 {"id":11290,"codability":1,"judgment":1,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L1","module":"生产执行"},
 {"id":20175,"codability":1,"judgment":1,"coordination":1,"accountability":1,"embodied":0,"hierarchy":"L2","module":"行政法务"},
 {"id":17949,"codability":0,"judgment":1,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L1","module":"设备维护"},
 {"id":2479,"codability":2,"judgment":0,"coordination":0,"accountability":0,"embodied":0,"hierarchy":"L0","module":"行政法务"},
 {"id":20615,"codability":1,"judgment":1,"coordination":1,"accountability":0,"embodied":1,"hierarchy":"L1","module":"市场"},
 {"id":14137,"codability":1,"judgment":0,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L1","module":"生产执行"},
 {"id":21196,"codability":0,"judgment":1,"coordination":1,"accountability":1,"embodied":0,"hierarchy":"L1","module":"人力资源"},
 {"id":4876,"codability":0,"judgment":1,"coordination":0,"accountability":0,"embodied":1,"hierarchy":"L1","module":"设备维护"},
 {"id":11199,"codability":0,"judgment":1,"coordination":1,"accountability":1,"embodied":0,"hierarchy":"L2","module":"综合管理"},
 {"id":1378,"codability":1,"judgment":1,"coordination":1,"accountability":0,"embodied":0,"hierarchy":"L1","module":"财务会计"},
 {"id":8588,"codability":0,"judgment":1,"coordination":1,"accountability":0,"embodied":0,"hierarchy":"L2","module":"人力资源"},
 {"id":23166,"codability":0,"judgment":1,"coordination":1,"accountability":1,"embodied":1,"hierarchy":"L1","module":"客户服务"},
 {"id":17487,"codability":0,"judgment":1,"coordination":1,"accountability":1,"embodied":1,"hierarchy":"L1","module":"客户服务"},
]

incsv = r"D:\harness office\research\jobtask-agent\out\anno_input\2019\batch_000.csv"
outp = r"D:\harness office\research\jobtask-agent\out\anno_output\2019\batch_000.json"

with open(incsv, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.reader(f))
header, data = rows[0], rows[1:]
assert header == ["id","text"], header
assert len(data) == len(annos), (len(data), len(annos))
csv_ids = [int(r[0]) for r in data]
ann_ids = [a["id"] for a in annos]
assert csv_ids == ann_ids, "id order mismatch"

keys = ["id","codability","judgment","coordination","accountability","embodied","hierarchy","module"]
mods = {"生产执行","质量检验","研发技术","工艺工程","设备维护","销售","市场","采购供应链","物流仓储","人力资源","财务会计","行政法务","IT数据","EHS安全","客户服务","综合管理","其他"}
for a in annos:
    assert list(a.keys()) == keys, a
    assert a["codability"] in (0,1,2)
    for k in ("judgment","coordination","accountability","embodied"):
        assert a[k] in (0,1)
    assert a["hierarchy"] in ("L0","L1","L2","L3")
    assert a["module"] in mods

os.makedirs(os.path.dirname(outp), exist_ok=True)
with open(outp, "w", encoding="utf-8", newline="\n") as f:
    json.dump(annos, f, ensure_ascii=False, indent=1)
raw = open(outp, "rb").read()
assert not raw.startswith(b"\xef\xbb\xbf"), "BOM found"
print("OK", len(annos))
