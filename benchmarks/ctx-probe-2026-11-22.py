"""Does qwen3:14b get faster at a smaller context? One model, four windows, one prompt.

The speed probe measured 19.1 tok/s for qwen3:14b while `ollama ps` reported **38 % CPU / 62 % GPU** at Ollama's
32,768 window. This probe asks the obvious follow-up: shrink the window until the weights and the KV cache fit, and
see what the spill was costing.

Throughput is the server's own `eval_count / eval_duration` (the lab's documented method), not wall time, so the
load and the prefill are not in the number. Placement comes from `/api/ps` (`size_vram / size`), because the text
of `ollama ps` is not something a check should parse.

  python benchmarks/ctx-probe-2026-11-22.py --model qwen3:14b --ctx 32768 16384 8192 4096
"""

import argparse
import json
import statistics
import sys
import time
import urllib.request

PROMPT = ("Write a single paragraph of about one hundred and fifty words describing a fishing harbour at "
          "dawn. No lists, no headings.")


def post(path, body, timeout=900):
    request = urllib.request.Request("http://127.0.0.1:11434" + path,
                                     data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def get(path):
    with urllib.request.urlopen("http://127.0.0.1:11434" + path, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def unload(model):
    post("/api/chat", {"model": model, "messages": [{"role": "user", "content": "x"}],
                       "stream": False, "keep_alive": 0, "options": {"num_predict": 1}})


def placement(model):
    for entry in get("/api/ps").get("models", []):
        if entry.get("name") == model or entry.get("model") == model:
            size = entry.get("size") or 0
            vram = entry.get("size_vram") or 0
            return (100.0 * vram / size if size else 0.0), size, vram
    return 0.0, 0, 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen3:14b")
    parser.add_argument("--ctx", type=int, nargs="+", default=[32768, 16384, 8192, 4096])
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--max-tokens", type=int, default=400)
    args = parser.parse_args()

    for ctx in args.ctx:
        unload(args.model)
        time.sleep(1)
        # load at this window and leave it warm for the measurements
        post("/api/chat", {"model": args.model, "messages": [{"role": "user", "content": "hi"}],
                           "stream": False, "options": {"num_ctx": ctx, "num_predict": 8}, "keep_alive": "10m"})
        share, size, vram = placement(args.model)
        post("/api/chat", {"model": args.model, "messages": [{"role": "user", "content": PROMPT}],
                          "stream": False, "options": {"num_ctx": ctx, "num_predict": 16}, "keep_alive": "10m"})
        rates = []
        for run in range(args.runs):
            reply = post("/api/chat", {"model": args.model,
                                       "messages": [{"role": "user", "content": PROMPT}],
                                       "stream": False,
                                       "options": {"num_ctx": ctx, "num_predict": args.max_tokens,
                                                   "temperature": 0},
                                       "keep_alive": "10m"})
            out = reply.get("eval_count") or 0
            duration = (reply.get("eval_duration") or 1) / 1e9
            rates.append(out / duration if duration else 0)
            print("  ctx %5d run %d: %d tokens, %.1f tok/s" % (ctx, run + 1, out, rates[-1]), file=sys.stderr)
        print("ctx %5d  %5.1f%% GPU  resident %5.1f GiB  generation %6.1f tok/s  (median of %s)"
              % (ctx, share, size / 1073741824, statistics.median(rates),
                 ", ".join("%.1f" % r for r in rates)))
    unload(args.model)


if __name__ == "__main__":
    main()
