"""check_hedging.py — 仓库文档防御性写作（hedging）检测。

词表来源：
  aproko/keyword_hedge_detector 的 chinese_hedges.csv（github.com/aproko/keyword_hedge_detector），
  过滤口语词（嗯/呃/这个/那个/某人等）后取技术文档相关的模糊限定与认知情态词，
  并补充英文 hedge 词（Hyland 1998 类别：content-oriented relational hedges）。
用法：python check_hedging.py [目录]   默认扫 gh_publish 下全部 .md
原则（GMU Writing Center / EAP Foundation 攻略）：hedging 只用于证据真正不确定处；
结论有数字支撑时不 hedge；强 claim 不配弱 support；模糊限定词一律删。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# A 级：弱化结论 / 模糊限定 —— 有数字或明确证据支撑时默认改写
A_LEVEL = [
    # HREL 认知情态（aproko 词表精选）
    "可能", "或许", "也许", "似乎", "看起来", "恐怕", "有可能", "未必",
    "不好说", "说不清", "据估计", "据说", "据传",
    # HPROP 模糊限定（aproko 词表精选）
    "某种程度上", "一定程度上", "某种意义上", "基本上是", "差不多", "大体上",
    "大概", "大致上", "多多少少", "或多或少", "部分地", "有所", "有点",
    # 自补：技术文档常见弱化句式
    "待验证", "待观察", "待补", "需要进一步", "有望", "相对较", "相对而言",
    "总的来说", "一般而言", "应该说", "可以说", "算是", "算得上", "倾向于",
]
# B 级：中性频率词 —— 描述真实波动/习惯性规律时合法，逐一判断
B_LEVEL = ["通常", "往往", "一般来说", "大概", "大致", "经常", "部分", "初步", "可能存在"]
# 英文 hedge
EN_LEVEL = [
    r"\bmay\b", r"\bmight\b", r"\bpossibly\b", r"\bpresumably\b", r"\bseems?\b",
    r"\bappears? to\b", r"\bsomewhat\b", r"\brelatively\b", r"\broughly\b",
    r"\bapproximately\b", r"\bpotentially\b", r"\blikely to\b", r"\bsuggests? that\b",
    r"\bfuture work\b", r"\bneeds? further\b", r"\bremains? to be\b",
]

PATTERNS = ([(w, "A", w) for w in A_LEVEL]
            + [(w, "B", w) for w in B_LEVEL]
            + [(p, "EN", p) for p in EN_LEVEL])


def scan(path: Path):
    hits = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return hits
    for i, ln in enumerate(lines, 1):
        for pat, lvl, disp in PATTERNS:
            for mo in re.finditer(pat, ln, flags=re.IGNORECASE if lvl == "EN" else 0):
                s = max(0, mo.start() - 25)
                frag = ln[s:mo.end() + 25].strip()
                hits.append((path.name, i, lvl, disp, frag))
    return hits


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "gh_publish"
    all_hits = []
    for f in sorted(root.rglob("*.md")):
        all_hits.extend(scan(f))
    from collections import Counter
    cnt = Counter((lvl, w) for _, _, lvl, w, _ in all_hits)
    print(f"=== 命中 {len(all_hits)} 处，词频 ===")
    for (lvl, w), c in cnt.most_common():
        print(f"  [{lvl}] {w}: {c}")
    print("\n=== 逐处明细 ===")
    for fn, ln, lvl, w, frag in all_hits:
        print(f"  {fn}:{ln} [{lvl}] “{w}”  …{frag}…")
