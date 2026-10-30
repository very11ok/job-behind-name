"""LLM 后端层：OpenAI 兼容接口 + API 池轮换 + 本地缓存 + 重试。

- 池来源：C:\\Users\\liuqin\\.dsh\\api-pool.yaml（或者环境变量 JTAGENT_ENDPOINTS='{...}'）
- 缓存：out/llm_cache/<sha256>.json —— 同一提示词永不重复计费
- 知识截止纪律：prompts 中注入 SYSTEM_CUTOFF，输出仅结构（任务 id / 概率 / 机制标签），
  不允许任何职业名称文本（检出即重抽）。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.request
import urllib.error
from pathlib import Path

OUT = Path(r"D:\harness office\research\jobtask-agent\out")
CACHE = OUT / "llm_cache"
POOL_FILE = Path(r"C:\Users\liuqin\.dsh\api-pool.yaml")

DEFAULT_MODEL = "tierflow"


def _load_pool(pool_file: Path = POOL_FILE) -> list[dict]:
    """极简 YAML 解析：只关心 entries 的 baseURL / apiKey / name / disabled。"""
    entries, cur = [], None
    for line in pool_file.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("- name:"):
            if cur:
                entries.append(cur)
            cur = {}
        elif cur is not None and ":" in s:
            k, _, v = s.partition(":")
            k, v = k.strip(), v.strip()
            if k in ("baseURL", "apiKey", "name", "disabled"):
                cur[k] = v
    if cur:
        entries.append(cur)
    out = []
    for e in entries:
        if e.get("disabled") == "true" or not e.get("apiKey") or not e.get("baseURL"):
            continue
        if e["baseURL"].count("chat/completions"):  # 归一化为 baseURL
            e["baseURL"] = re.sub(r"/chat/completions.*$", "", e["baseURL"])
        out.append({"base_url": e["baseURL"], "api_key": e["apiKey"], "name": e.get("name", "")})
    env = os.environ.get("JTAGENT_ENDPOINTS")
    if env:
        out = json.loads(env) + out
    if not out:
        raise RuntimeError("api-pool 里没有可用 endpoint；请设置 JTAGENT_ENDPOINTS")
    return out


class LLMClient:
    """OpenAI 兼容 chat.completions 客户端：轮换 + 缓存 + 重试。"""

    def __init__(self, model: str = DEFAULT_MODEL, cache_dir: Path = CACHE,
                 timeout: int = 60, max_retries: int = 2, log_path: Path | None = None):
        self.model = model
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.max_retries = max_retries
        self.endpoints = _load_pool()
        self.dead: set[int] = set()
        self.stats = {"calls": 0, "cache_hits": 0, "tokens": 0, "errors": 0}
        self.log_path = log_path or (self.cache_dir / "llm_calls.jsonl")

    def _key(self, messages, model, temperature, schema) -> str:
        h = hashlib.sha256()
        h.update(json.dumps([messages, model, temperature, schema], ensure_ascii=False,
                            sort_keys=True).encode())
        return h.hexdigest()[:32]

    def chat(self, messages, model: str | None = None, temperature: float = 0.0,
             max_tokens: int = 4000, schema: str = "chat", use_cache: bool = True) -> dict:
        model = model or self.model
        ck = self._key(messages, model, temperature, schema)
        cf = self.cache_dir / f"{ck}.json"
        if use_cache and cf.exists():
            self.stats["cache_hits"] += 1
            return json.loads(cf.read_text(encoding="utf-8"))

        body = {"model": model, "messages": messages,
                "temperature": temperature, "max_tokens": max_tokens}
        last_err = None
        for attempt in range(self.max_retries + 1):
            for i, ep in enumerate(self.endpoints):
                if i in self.dead:
                    continue
                req = urllib.request.Request(
                    ep["base_url"] + "/chat/completions",
                    data=json.dumps(body).encode(),
                    headers={"Authorization": "Bearer " + ep["api_key"],
                             "Content-Type": "application/json"})
                try:
                    t0 = time.time()
                    with urllib.request.urlopen(req, timeout=self.timeout) as r:
                        d = json.loads(r.read())
                    if "error" in d:  # 流式错误被散装返回
                        raise RuntimeError(str(d["error"]))
                    out = {"content": d["choices"][0]["message"]["content"],
                           "usage": d.get("usage", {}), "endpoint": ep["name"],
                           "seconds": time.time() - t0}
                    self.stats["calls"] += 1
                    self.stats["tokens"] += out["usage"].get("total_tokens", 0)
                    if use_cache:
                        cf.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
                    return out
                except urllib.error.HTTPError as e:
                    code = e.code
                    detail = ""
                    try:
                        detail = e.read().decode("utf-8", "ignore")[:200]
                    except Exception:
                        pass
                    last_err = f"HTTP {code} {detail}"
                    if code in (401, 403, 402) or "balance" in detail or "quota" in detail:
                        self.dead.add(i)
                        break
                except Exception as e:
                    last_err = str(e)[:200]
            time.sleep(1.5 * (attempt + 1))
        self.stats["errors"] += 1
        raise RuntimeError(f"all endpoints failed: {last_err}")

    def chat_json(self, messages, required_keys: list[str], model=None, temperature=0.0,
                  max_tokens=4000, schema="json") -> list:
        """调用并解析 JSON 数组输出；失败重抽一次。"""
        for retry in range(2):
            out = self.chat(messages, model=model, temperature=temperature if retry == 0 else 0.3,
                            max_tokens=max_tokens, schema=schema)
            try:
                txt = out["content"].strip()
                txt = re.sub(r"^```(json)?|```$", "", txt, flags=re.MULTILINE).strip()
                data = json.loads(txt)
                if isinstance(data, dict) and len(data) == 1:
                    data = next(iter(data.values()))
                if isinstance(data, list) and all(
                        isinstance(x, dict) and all(k in x for k in required_keys) for x in data):
                    return data
            except Exception:
                continue
        raise ValueError(f"JSON 解析失败（required={required_keys}）: {out['content'][:300]}")
