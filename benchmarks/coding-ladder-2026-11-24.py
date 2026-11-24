#!/usr/bin/env python3
"""APPS coding ladder: one difficulty tier at a time, graded by running the test cases.

APPS (codeparrot/apps) ships every problem with an official difficulty label -
introductory / interview / competition - and stdin/stdout test cases, so a tier step
is a ~50% difficulty step rather than a guess. A solution is only counted when every
test case for that problem passes; a wrong answer, a timeout and a crash all count
as a failure, and the reason is recorded so a failure can be read later.

Usage:
  python coding-ladder-2026-11-24.py --tier interview --model qwen3-coder:30b \
      --base-url http://127.0.0.1:8090 --limit 8 --out results/coding-interview.json
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

APPS = pathlib.Path(r"D:/build/apps/test.jsonl")
TIERS = ("introductory", "interview", "competition")


def post(url: str, payload: dict, timeout: int = 900) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url + "/v1/chat/completions", data=body,
                                headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def ask_ollama(base_url: str, model: str, messages: list[dict], max_tokens: int,
               temperature: float, num_ctx: int, timeout: int) -> dict:
    """Native /api/chat: the only endpoint that can switch thinking off for qwen3.x.

    Without this the model spends the whole answer budget on reasoning and returns no
    code, which measures the harness rather than the model.
    """
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
                      "prompt_tokens": m.get("prompt_eval_count")},
            "thinking": len((m.get("message") or {}).get("thinking") or "")}


def load_items(tier: str, limit: int, offset: int) -> list[dict]:
    """Stream the split and keep graded problems of one tier, in file order.

    Two filters keep each run bounded without changing what is being measured:
    at most five test cases, and a statement that fits the context we run at.
    """
    out: list[dict] = []
    seen = 0
    with APPS.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("difficulty") != tier:
                continue
            io = row.get("input_output")
            if not io:
                continue  # ungraded problem: cannot be scored mechanically
            try:
                cases = json.loads(io)
            except json.JSONDecodeError:
                continue
            ins, outs = cases.get("inputs") or [], cases.get("outputs") or []
            if not ins or len(ins) != len(outs) or len(ins) > 5:
                continue
            q = row.get("question") or ""
            if len(q) > 6000:
                continue
            seen += 1
            if seen <= offset:
                continue
            out.append({"id": seen, "question": q, "inputs": ins, "outputs": outs,
                        "difficulty": tier})
            if len(out) >= limit:
                break
    return out


def same_output(got: str, want: str) -> bool:
    """APPS expected outputs carry trailing spaces on most lines, so compare line-wise.

    Comparing whole strings would fail a correct program for whitespace the task never
    asked about - measured: three of six introductory failures were exactly that.
    """
    def norm(s: str) -> list[str]:
        lines = [ln.rstrip() for ln in (s or "").replace("\r\n", "\n").split("\n")]
        while lines and not lines[-1]:
            lines.pop()
        return lines
    return norm(got) == norm(want)


CODE_RE = re.compile(r"```(?:python3?|py)?\s*\n(.*?)```", re.S)


def extract_code(text: str) -> tuple[str, str]:
    blocks = CODE_RE.findall(text or "")
    if blocks:
        return blocks[-1].strip(), "fenced"
    stripped = (text or "").strip()
    if stripped.startswith(("import ", "from ", "def ", "n = ", "#")) or "\n" in stripped:
        return stripped, "bare"
    return "", "no code found"


def run_case(code: str, stdin_text: str, timeout: float, workdir: str) -> tuple[bool, str]:
    script = os.path.join(workdir, "sol.py")
    with open(script, "w", encoding="utf-8") as fh:
        fh.write(code + "\n")
    try:
        p = subprocess.run([sys.executable, script], input=stdin_text, text=True,
                           capture_output=True, timeout=timeout, cwd=workdir)
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:  # noqa: BLE001 - any launch failure is a failed case
        return False, f"launch: {type(e).__name__}"
    if p.returncode != 0:
        return False, f"exit {p.returncode}: {(p.stderr or '').strip().splitlines()[-1][:90] if p.stderr else ''}"
    return True, p.stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8090")
    ap.add_argument("--model", required=True)
    ap.add_argument("--tier", default="interview", choices=TIERS)
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--case-timeout", type=float, default=6.0)
    ap.add_argument("--api", default="openai", choices=("openai", "ollama"),
                    help="ollama = native /api/chat with thinking disabled")
    ap.add_argument("--num-ctx", type=int, default=8192)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    items = load_items(args.tier, args.limit, args.offset)
    if not items:
        print(f"no usable {args.tier} problems found at offset {args.offset}")
        return 2

    sysmsg = ("You write correct Python 3 programs. Read the problem, then reply with ONE "
              "```python block containing a complete program that reads stdin and writes stdout. "
              "No explanation, no tests, no example runs.")
    rows, passed, t0 = [], 0, time.time()
    for it in items:
        prompt = f"{it['question']}\n\nWrite a complete Python 3 solution that reads from stdin and writes to stdout."
        t1 = time.time()
        msgs = [{"role": "system", "content": sysmsg},
                {"role": "user", "content": prompt}]
        try:
            if args.api == "ollama":
                r = ask_ollama(args.base_url, args.model, msgs, args.max_tokens,
                               args.temperature, args.num_ctx, 1800)
                content, finish, usage = r["content"], r["finish"], r["usage"]
                think_chars = r["thinking"]
            else:
                resp = post(args.base_url, {"model": args.model, "messages": msgs,
                                            "max_tokens": args.max_tokens,
                                            "temperature": args.temperature})
                choice = resp["choices"][0]
                content = (choice.get("message") or {}).get("content") or ""
                finish = choice.get("finish_reason")
                usage = resp.get("usage") or {}
                think_chars = 0
        except Exception as e:  # noqa: BLE001
            rows.append({"id": it["id"], "ok": False, "why": f"request: {type(e).__name__}"})
            print(f"#{it['id']:>2} request failed: {type(e).__name__}", flush=True)
            continue
        secs = time.time() - t1
        code, how = extract_code(content)
        if not code:
            rows.append({"id": it["id"], "ok": False, "why": how, "finish": finish,
                         "seconds": round(secs, 1), "usage": usage,
                         "thinking_chars": think_chars, "raw": content[:300]})
            print(f"#{it['id']:>2} FAIL {how}", flush=True)
            continue
        with tempfile.TemporaryDirectory() as wd:
            case_ok, detail = 0, []
            for stdin_text, want in zip(it["inputs"], it["outputs"]):
                ok, got = run_case(code, stdin_text, args.case_timeout, wd)
                if ok and same_output(got, want):
                    case_ok += 1
                else:
                    detail.append("timeout" if got == "timeout" else
                                  f"want={want.rstrip()[:40]!r} got={str(got).rstrip()[:40]!r}")
            ok = case_ok == len(it["inputs"])
        passed += ok
        rows.append({"id": it["id"], "ok": ok, "cases": f"{case_ok}/{len(it['inputs'])}",
                     "how": how, "why": "" if ok else "; ".join(detail[:2]),
                     "finish": finish, "seconds": round(secs, 1), "usage": usage,
                     "code_chars": len(code), "thinking_chars": think_chars,
                     "raw": content[:300]})
        print(f"#{it['id']:>2} {'PASS' if ok else 'FAIL'} cases={case_ok}/{len(it['inputs'])} "
              f"{secs:5.1f}s {'' if ok else rows[-1]['why'][:80]}", flush=True)

    total = len(items)
    out = {"model": args.model, "tier": args.tier, "offset": args.offset,
           "passed": passed, "possible": total, "rate": round(passed / total, 3),
           "seconds": round(time.time() - t0, 1), "rows": rows,
           "note": "APPS test split; a problem counts only when every test case passes; "
                   "graded by executing the model's program, not by reading it."}
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\n{args.model} | APPS {args.tier} | {passed}/{total} = {100*passed/total:.0f}%")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
