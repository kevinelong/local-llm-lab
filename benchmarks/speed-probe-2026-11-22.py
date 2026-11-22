"""One prompt, one budget, three runs - generation and prompt rates for any OpenAI-compatible endpoint.

Why separate from the quality pass: that battery was about correctness, and its timings are not usable (the
first Inkling run served from an instance that had degraded to 5.4 t/s). This probe does one thing - the same
request, repeated - and reports throughput from the server's own token counts, so the three models are
compared on identical work.

  python benchmarks/speed-probe-2026-11-22.py --base-url http://127.0.0.1:8080 --model inkling --runs 3
"""

import argparse
import json
import statistics
import sys
import time
import urllib.request

PROMPT = ("Write a single paragraph of about one hundred and fifty words describing a fishing harbour at "
          "dawn. No lists, no headings.")


def call(base_url, model, max_tokens, timeout=600):
    body = {"model": model, "messages": [{"role": "user", "content": PROMPT}],
            "temperature": 0, "max_tokens": max_tokens, "stream": False}
    request = urllib.request.Request(base_url.rstrip("/") + "/v1/chat/completions",
                                     data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
    started = time.time()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    elapsed = time.time() - started
    usage = payload.get("usage") or {}
    return elapsed, usage.get("completion_tokens") or 0, usage.get("prompt_tokens") or 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--max-tokens", type=int, default=400)
    args = parser.parse_args()

    call(args.base_url, args.model, 16)          # warmup: load, allocate, do not measure
    rates, prompts = [], []
    for run in range(args.runs):
        elapsed, out_tokens, in_tokens = call(args.base_url, args.model, args.max_tokens)
        rate = out_tokens / elapsed if elapsed else 0
        rates.append(rate)
        prompts.append(in_tokens)
        print("run %d: %d tokens in %.1f s = %.1f tok/s (prompt %d tokens)"
              % (run + 1, out_tokens, elapsed, rate, in_tokens), file=sys.stderr)
    print("%-28s generation %.1f tok/s (median of %s)" % (args.model, statistics.median(rates),
                                                          ", ".join("%.1f" % r for r in rates)))


if __name__ == "__main__":
    main()
