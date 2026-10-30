"""全量上传：数据 + 过程 + 脚本 + 文档 → very11ok/job-behind-name。

分两个 manifest：
  CORE  — README、docs、scripts、data/{objects,snapshots,results,judge_input,anno_*}（约 60MB）
  PAIRS — data/pairs/*.parquet（9 个大文件，30–46MB each）
排除：研究文稿（paper_dump/proposal_dump/dump_docx）、__pycache__、.tmp_anno、gh_publish 自身。
token 只从环境变量 GH_TOKEN 读取。
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = "job-behind-name"
OWNER = "very11ok"
SRC = Path(r"D:\harness office\research\jobtask-agent")
WF = Path(r"D:\zcode office\.zcode\workflow-drafts\pipeline.dwf.ts")

# ── manifest 构建 ────────────────────────────────────────────────
CORE: list[tuple[Path, str]] = []
PAIRS: list[tuple[Path, str]] = []


def add(local: Path, repo: str):
    if local.exists():
        CORE.append((local, repo))
    else:
        print(f"MISSING: {local}")


add(SRC / "gh_publish" / "README.md", "README.md")
add(SRC / "gh_publish" / "docs" / "workflow.md", "docs/workflow.md")
add(SRC / "report.md", "docs/report.md")
add(WF, "scripts/workflow/pipeline.dwf.ts")

# 根目录脚本（排除文稿工具）
for f in sorted(SRC.glob("*.py")):
    if f.name == "dump_docx.py":
        continue
    add(f, f"scripts/{f.name}")

# jtagent 库
for f in sorted((SRC / "jtagent").glob("*.py")):
    add(f, f"scripts/jtagent/{f.name}")

# out 下数据与过程材料
def add_tree(local_dir: Path, repo_dir: str, exts: set[str]):
    for f in sorted(local_dir.rglob("*")):
        if f.is_file() and f.suffix.lower() in exts and "__pycache__" not in f.parts:
            rel = f.relative_to(local_dir).as_posix()
            CORE.append((f, f"{repo_dir}/{rel}"))

add_tree(SRC / "out" / "objects", "data/objects", {".parquet"})
add_tree(SRC / "out" / "snapshots", "data/snapshots", {".parquet"})
add_tree(SRC / "out" / "judge_input", "data/judge_input", {".txt"})
add_tree(SRC / "out" / "anno_input", "data/anno_input_2019", {".csv", ".py"})
add_tree(SRC / "out" / "anno_output", "data/anno_output_2019", {".csv", ".py", ".parquet"})
add(SRC / "out" / "pair_judge_truth.parquet", "data/pair_judge_truth.parquet")

# results：md → docs/results，其余 → data/results
for f in sorted((SRC / "out" / "results").iterdir()):
    if not f.is_file():
        continue
    if f.suffix == ".md":
        add(f, f"docs/results/{f.name}")
    else:
        add(f, f"data/results/{f.name}")

# pairs 大文件
for f in sorted((SRC / "out" / "pairs").glob("*.parquet")):
    PAIRS.append((f, f"data/pairs/{f.name}"))

# ── 上传 ─────────────────────────────────────────────────────────
def gh_api(path: str, method: str = "GET", data: dict | None = None,
           timeout: int = 60) -> tuple[int, dict | str]:
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        print("ERROR: GH_TOKEN not set", file=sys.stderr)
        sys.exit(1)
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"
    headers = {"Authorization": f"Bearer {token}",
               "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28"}
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw
    except Exception as e:
        return 0, str(e)


def upload_one(local: Path, repo_rel: str, timeout: int, retries: int = 2) -> bool:
    for attempt in range(retries + 1):
        try:
            b64 = base64.b64encode(local.read_bytes()).decode("ascii")
            status, resp = gh_api(repo_rel, "GET", timeout=timeout)
            sha = resp.get("sha") if isinstance(resp, dict) and status == 200 else None
            data = {"message": f"[full-upload] {repo_rel}", "content": b64}
            if sha:
                data["sha"] = sha
            status, resp = gh_api(repo_rel, "PUT", data, timeout=timeout)
            if status in (200, 201):
                return True
            print(f"  FAIL({status}): {repo_rel} - {str(resp)[:200]}")
        except Exception as e:
            print(f"  EXC: {repo_rel} - {e}")
        time.sleep(3)
    return False


def run(manifest, label):
    ok = fail = 0
    t0 = time.time()
    print(f"=== {label}: {len(manifest)} files ===")
    for i, (local, repo_rel) in enumerate(manifest, 1):
        size = local.stat().st_size
        timeout = 300 if size > 5_000_000 else 60
        good = upload_one(local, repo_rel, timeout)
        ok += good
        fail += (not good)
        if good and (i % 10 == 0 or i == len(manifest) or size > 1_000_000):
            print(f"[{i}/{len(manifest)}] {repo_rel} ({size / 1e6:.2f}MB) "
                  f"ok={ok} fail={fail} elapsed={time.time() - t0:.0f}s")
    print(f"=== {label} done: ok={ok} fail={fail} in {time.time() - t0:.0f}s ===")
    return fail


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    sl = sys.argv[2] if len(sys.argv) > 2 else None  # 形如 0:150 的切片
    total_fail = 0
    if which in ("core", "all"):
        m = CORE
        if sl:
            a, b = sl.split(":")
            m = CORE[int(a):int(b)]
        total_fail += run(m, f"CORE[{sl or 'all'}]")
    if which in ("pairs", "all"):
        m = PAIRS
        if sl:
            a, b = sl.split(":")
            m = PAIRS[int(a):int(b)]
        total_fail += run(m, f"PAIRS[{sl or 'all'}]")
    print(f"\nTOTAL FAILURES: {total_fail}")
    sys.exit(0 if total_fail == 0 else 2)
