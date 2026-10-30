"""用 Git Data API 上传 >40MB 的大文件（Contents API 40MB 限制，blob API 100MB）。

流程：blobs → tree（基于当前 main tree）→ commit → 更新 refs/heads/main。
一次 commit 打包全部剩余文件。
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

OWNER, REPO = "very11ok", "job-behind-name"
BRANCH = "main"
SRC = Path(r"D:\harness office\research\jobtask-agent")

FILES = [
    ("out/pairs/pairs_2018.parquet", "data/pairs/pairs_2018.parquet"),
    ("out/pairs/pairs_2021.parquet", "data/pairs/pairs_2021.parquet"),
    ("out/pairs/pairs_2022.parquet", "data/pairs/pairs_2022.parquet"),
    ("out/pairs/pairs_2024.parquet", "data/pairs/pairs_2024.parquet"),
    ("out/pairs/pairs_2025.parquet", "data/pairs/pairs_2025.parquet"),
]


def api(path: str, method: str = "GET", data: dict | None = None, timeout: int = 300):
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        sys.exit("ERROR: GH_TOKEN not set")
    url = f"https://api.github.com{path}"
    headers = {"Authorization": f"Bearer {token}",
               "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28"}
    body = json.dumps(data).encode() if data is not None else None
    if body:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read().decode()
                return r.status, json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            raw = e.read().decode(errors="replace")
            try:
                return e.code, json.loads(raw)
            except json.JSONDecodeError:
                return e.code, raw
        except Exception as e:
            print(f"  net retry {attempt + 1}: {e}")
            time.sleep(5)
    return 0, "network failed"


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    # 1. 当前分支头
    s, ref = api(f"/repos/{OWNER}/{REPO}/git/ref/heads/{BRANCH}")
    if s != 200:
        sys.exit(f"ref failed: {ref}")
    head_commit = ref["object"]["sha"]
    print(f"head commit: {head_commit}")

    s, commit = api(f"/repos/{OWNER}/{REPO}/git/commits/{head_commit}")
    base_tree = commit["tree"]["sha"]
    print(f"base tree: {base_tree}")

    # 2. blobs
    tree_items = []
    for local_rel, repo_rel in FILES:
        local = SRC / local_rel
        size = local.stat().st_size
        print(f"blob {repo_rel} ({size / 1e6:.1f}MB)...", flush=True)
        b64 = base64.b64encode(local.read_bytes()).decode("ascii")
        s, blob = api(f"/repos/{OWNER}/{REPO}/git/blobs", "POST",
                      {"content": b64, "encoding": "base64"}, timeout=600)
        if s != 201:
            print(f"  BLOB FAIL({s}): {repo_rel} - {str(blob)[:200]}")
            continue
        print(f"  blob sha {blob['sha'][:12]}")
        tree_items.append({"path": repo_rel, "mode": "100644",
                           "type": "blob", "sha": blob["sha"]})

    if not tree_items:
        sys.exit("nothing to commit")

    # 3. tree
    s, tree = api(f"/repos/{OWNER}/{REPO}/git/trees", "POST",
                  {"base_tree": base_tree, "tree": tree_items})
    if s != 201:
        sys.exit(f"tree failed: {str(tree)[:300]}")
    print(f"new tree: {tree['sha'][:12]}")

    # 4. commit
    msg = "[full-upload] data/pairs large parquet files via Git Data API"
    s, newc = api(f"/repos/{OWNER}/{REPO}/git/commits", "POST",
                  {"message": msg, "tree": tree["sha"], "parents": [head_commit]})
    if s != 201:
        sys.exit(f"commit failed: {str(newc)[:300]}")
    print(f"new commit: {newc['sha'][:12]}")

    # 5. 更新分支
    s, r = api(f"/repos/{OWNER}/{REPO}/git/refs/heads/{BRANCH}", "PATCH",
               {"sha": newc["sha"], "force": False})
    print(f"branch update: {s} {'OK' if s == 200 else str(r)[:200]}")

    print(f"\ndone: {len(tree_items)}/{len(FILES)} files committed")


if __name__ == "__main__":
    main()
