#!/usr/bin/env python3
"""LiveCodeBench ladder: one difficulty band at a time, graded by running the tests.

LCB publishes no Codeforces rating in the released data - the difficulty axis is the
three bands (easy / medium / hard), so a step between bands is the 50%-harder step this
ladder can honestly take. Problems are atcoder (stdin/stdout) or leetcode (call a named
function), and each ships public and private cases; both are used, the private ones being
a zlib+base64 blob.

Grading differs from APPS in one way that must not be forgotten when reading the numbers:
a problem counts only if every case passes on the FIRST program, with no partial credit
inside a case and no retry - the same bar LCB's pass@1 uses.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
import zlib

LCB = pathlib.Path(r"D:/build/lcb/test6.jsonl")
BANDS = ("easy", "medium", "hard")


def ask_ollama(base_url: str, model: str, messages: list[dict], max_tokens: int,
               temperature: float, num_ctx: int, timeout: int) -> dict:
    payload = {"model": model, "messages": messages, "stream": False, "think": False,
               "options": {"num_ctx": num_ctx, "num_predict": max_tokens,
                           "temperature": temperature}}
    req = urllib.request.Request(base_url + "/api/chat",
                                 data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        m = json.loads(r.read().decode("utf-8"))
    return {"content": (m.get("message") or {}).get("content") or "",
            "finish": m.get("done_reason"),
            "usage": {"completion_tokens": m.get("eval_count"),
                      "prompt_tokens": m.get("prompt_eval_count")}}


def cases_of(row: dict) -> list[dict]:
    """Public and private cases as one list; private is a compressed blob."""
    out: list[dict] = []
    for key in ("public_test_cases", "private_test_cases"):
        raw = row.get(key)
        if not raw:
            continue
        if key == "private_test_cases":
            try:
                raw = zlib.decompress(base64.b64decode(raw)).decode("utf-8")
            except Exception:
                continue
        try:
            for c in json.loads(raw):
                if c.get("input") is not None and c.get("output") is not None:
                    out.append({"input": c["input"], "output": c["output"],
                                "kind": c.get("testtype", "stdin")})
        except Exception:
            continue
    return out


def load_items(band: str, limit: int, offset: int, max_cases: int) -> list[dict]:
    items, seen = [], 0
    with LCB.open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("difficulty") != band:
                continue
            cases = cases_of(row)
            if not cases or len(cases) > max_cases:
                continue  # bounded so one run stays inside the job deadline
            content = row.get("question_content") or ""
            if len(content) > 6000:
                continue
            seen += 1
            if seen <= offset:
                continue
            func = ""
            try:
                func = (json.loads(row.get("metadata") or "{}") or {}).get("func_name") or ""
            except Exception:
                pass
            items.append({"id": row.get("question_id"), "title": row.get("question_title"),
                          "platform": row.get("platform"), "content": content,
                          "starter": row.get("starter_code") or "", "func": func,
                          "cases": cases, "band": band})
            if len(items) >= limit:
                break
    return items


CODE_RE = re.compile(r"```(?:python3?|py)?\s*\n(.*?)```", re.S)


def extract_code(text: str) -> tuple[str, str]:
    blocks = CODE_RE.findall(text or "")
    if blocks:
        return blocks[-1].strip(), "fenced"
    s = (text or "").strip()
    if s.startswith(("import ", "from ", "def ", "class ")) or "\n" in s:
        return s, "bare"
    return "", "no code found"


def norm(s: str) -> list[str]:
    lines = [ln.rstrip() for ln in (s or "").replace("\r\n", "\n").split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return lines


def run_stdin(code: str, stdin_text: str, timeout: float, wd: str) -> tuple[bool, str]:
    script = os.path.join(wd, "sol.py")
    with open(script, "w", encoding="utf-8") as fh:
        fh.write(code + "\n")
    try:
        p = subprocess.run([sys.executable, script], input=stdin_text, text=True,
                           capture_output=True, timeout=timeout, cwd=wd)
    except subprocess.TimeoutExpired:
        return False, "timeout"
    if p.returncode != 0:
        tail = (p.stderr or "").strip().splitlines()
        return False, f"exit {p.returncode}: {tail[-1][:80] if tail else ''}"
    return True, p.stdout


HARNESS = r"""
import json, sys
src = open("sol.py", encoding="utf-8").read()
ns = {"__name__": "sol"}
exec(compile(src, "sol.py", "exec"), ns)
name = %(func)r
fn = ns.get(name)
if fn is None and "Solution" in ns:
    fn = getattr(ns["Solution"](), name, None)
if fn is None:
    print(json.dumps({"error": "function " + name + " not defined"})); sys.exit(0)
args = json.loads(sys.stdin.read())
if not isinstance(args, list):
    args = [args]
# LCB renders leetcode inputs as the argument list, but several starters take the whole
# payload as one argument, so try the list unpacked and then packed before giving up.
calls = [lambda: fn(*args), lambda: fn(args)]
last = None
for call in calls:
    try:
        out = call()
    except TypeError as e:
        last = e
        continue
    except Exception as e:
        print(json.dumps({"error": type(e).__name__ + ": " + str(e)[:80]})); sys.exit(0)
    print(json.dumps({"ok": out}, default=str)); sys.exit(0)
print(json.dumps({"error": "TypeError: " + str(last)[:80]}))
"""


def run_functional(code: str, func: str, arg_json: list, want: str,
                   timeout: float, wd: str) -> tuple[bool, str]:
    script = os.path.join(wd, "sol.py")
    prompt = os.path.join(wd, "call.py")
    with open(script, "w", encoding="utf-8") as fh:
        fh.write(code + "\n")
    with open(prompt, "w", encoding="utf-8") as fh:
        fh.write(HARNESS % {"func": func})
    try:
        p = subprocess.run([sys.executable, prompt], input=json.dumps(arg_json), text=True,
                           capture_output=True, timeout=timeout, cwd=wd)
    except subprocess.TimeoutExpired:
        return False, "timeout"
    if p.returncode != 0:
        tail = (p.stderr or "").strip().splitlines()
        return False, f"exit {p.returncode}: {tail[-1][:80] if tail else ''}"
    try:
        got = json.loads((p.stdout or "").strip().splitlines()[-1])
    except Exception:
        return False, "unparsable harness output"
    if "error" in got:
        return False, got["error"]
    try:
        expected = json.loads(want)
    except Exception:
        expected = want
    return got.get("ok") == expected, f"got={str(got.get('ok'))[:40]}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:11434")
    ap.add_argument("--model", required=True)
    ap.add_argument("--band", default="medium", choices=BANDS)
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--max-cases", type=int, default=8)
    ap.add_argument("--max-tokens", type=int, default=6000)
    ap.add_argument("--num-ctx", type=int, default=8192)
    ap.add_argument("--case-timeout", type=float, default=6.0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    items = load_items(args.band, args.limit, args.offset, args.max_cases)
    if not items:
        print("no usable problems"); return 2

    sysmsg = ("You write correct Python 3 programs. Read the problem, then reply with ONE "
              "```python block. No explanation, no tests, no example runs.")
    rows, passed, t0 = [], 0, time.time()
    for it in items:
        ask = (it["content"] + "\n\n" + it["starter"]).strip() if it["starter"] else it["content"]
        if it["platform"] == "leetcode" and it["func"]:
            ask += f"\n\nDefine a Python function named `{it['func']}` that takes the arguments described and returns the answer. Do not read stdin."
        else:
            ask += "\n\nRead from stdin and write to stdout."
        t1 = time.time()
        try:
            r = ask_ollama(args.base_url, args.model,
                           [{"role": "system", "content": sysmsg},
                            {"role": "user", "content": ask}],
                           args.max_tokens, 0.0, args.num_ctx, 1800)
            content, finish, usage = r["content"], r["finish"], r["usage"]
        except Exception as e:  # noqa: BLE001
            rows.append({"id": it["id"], "ok": False, "why": f"request: {type(e).__name__}"})
            print(f"{it['id']} request failed: {type(e).__name__}", flush=True)
            continue
        secs = time.time() - t1
        code, how = extract_code(content)
        if not code:
            rows.append({"id": it["id"], "ok": False, "why": how, "finish": finish,
                         "seconds": round(secs, 1), "usage": usage, "raw": content[:300]})
            print(f"{it['id']} FAIL {how}", flush=True)
            continue
        ok_cases, detail = 0, []
        with tempfile.TemporaryDirectory() as wd:
            for c in it["cases"]:
                if c["kind"] == "functional" and it["func"]:
                    try:
                        argv = json.loads(c["input"])
                    except Exception:
                        argv = [c["input"]]
                    ok, got = run_functional(code, it["func"], argv, c["output"],
                                             args.case_timeout, wd)
                    matched = ok and got and not got.startswith("got=")
                else:
                    ok, got = run_stdin(code, c["input"], args.case_timeout, wd)
                    matched = ok and norm(got) == norm(c["output"])
                if matched:
                    ok_cases += 1
                else:
                    detail.append(f"{c['kind']}: want={str(c['output'])[:30]!r} "
                                  f"got={str(got)[:40]!r}")
        ok_all = ok_cases == len(it["cases"])
        passed += ok_all
        rows.append({"id": it["id"], "ok": ok_all, "cases": f"{ok_cases}/{len(it['cases'])}",
                     "platform": it["platform"], "why": "" if ok_all else "; ".join(detail[:2]),
                     "finish": finish, "seconds": round(secs, 1), "usage": usage,
                     "code_chars": len(code), "raw": content[:300]})
        print(f"{it['id']:<16} {'PASS' if ok_all else 'FAIL'} "
              f"cases={ok_cases}/{len(it['cases'])} {secs:5.1f}s "
              f"{'' if ok_all else rows[-1]['why'][:70]}", flush=True)

    total = len(items)
    out = {"model": args.model, "benchmark": "livecodebench-v6", "band": args.band,
           "offset": args.offset, "passed": passed, "possible": total,
           "rate": round(passed / total, 3), "seconds": round(time.time() - t0, 1),
           "rows": rows,
           "note": "LCB v6, public+private cases, pass@1: a problem counts only if every case "
                   "passes on the first program; no partial credit, no retry."}
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\n{args.model} | LCB {args.band} | {passed}/{total} = {100*passed/total:.0f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
