"""Quality pass: the same ten tasks, the same flags, the same scorer for every model.

Written 2026-11-22 to place Inkling 2 Mini against the store's recommend-able dense models
(qwen3:8b, qwen3:14b). Two rules from `skill://lab-evidence-discipline` shape it:

  * every task runs `--runs` times and the result is reported as a vector, never a single observation;
  * nothing in here is model-specific. Same prompts, same temperature, same token budget, same scorer, so a
    comparison across models is a comparison of models.

Scoring is mechanical wherever it can be: exact numbers, a JSON parse, a word count, and - for the code task -
the function is **executed** against known answers rather than eyeballed. Two tasks need judgement (the
uncertainty probe and the summary), and those use a stated rule in code, not a vibe.

Usage:
  python benchmarks/quality-pass-2026-11-22.py --base-url http://127.0.0.1:8080 --model <id> \
      --label inkling --out results/quality-inkling.json [--runs 3] [--max-tokens 640]
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

# ---------------------------------------------------------------- the tasks

PASSAGE = (
    "The night ferry left Ardmore at 06:40 with twelve crates of seed potatoes aboard. The manifest was "
    "signed by the harbourmaster, Ifeanyi Okafor, who noted a tide of 2.4 metres and a swell running from "
    "the south-west. The crossing took ninety minutes, and the crates were unloaded at Kilronan before the "
    "market opened."
)

NEEDLE_LEAD = (
    "The archive room had been closed since the flood, and the clerks worked from a temporary office above "
    "the chandlery. Boxes stood three deep against the wall, each labelled in a hand that had long since "
    "stopped being legible to anyone but its owner. The catalogue was typed on a machine that had lost its "
    "capital E, so every heading read as though it had been whispered. Visitors were asked not to touch the "
    "ledgers without gloves, and not to linger in the aisles after four, when the light came through the "
    "western windows and made the dust look like weather. "
)

NEEDLE = "The custodian's access code was Azure-4471, changed every quarter and written on nothing."

NEEDLE_TAIL = (
    " In practice the code was shared over the telephone, and the custodian had twice been reminded that this "
    "was not procedure. The room itself was unremarkable: a radiator, six shelves, a chair with one arm, and "
    "a window that never quite shut. The clerks agreed the archive was less an institution than a habit, and "
    "the habit was to leave the door locked and the light on."
)

SUMMARY_TEXT = (
    "The village council voted on Tuesday to rebuild the old pier with stone rather than timber, a decision "
    "that reversed its own ruling from the previous spring. Supporters argued the stone would outlast three "
    "generations of ratepayers; opponents said the cost would fall on the fishermen who used the pier daily "
    "and could least afford it. The works are due to begin after the herring season, subject to a survey that "
    "has not yet been commissioned."
)


def tasks():
    """The battery: (name, prompt, scorer). Order is fixed so two runs are comparable row by row."""
    return [
        ("bat_ball",
         "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. "
         "How much does the ball cost? Answer with the amount only.",
         score_ball),
        ("planets",
         "List the eight planets of the solar system in order from the Sun, one per line, nothing else.",
         score_planets),
        ("extract_count",
         PASSAGE + "\n\nHow many crates were aboard the ferry? Answer with the number only.",
         lambda a, c: hit(a, r"\b12\b", "12")),
        ("json_shape",
         'Reply with only a JSON object and nothing else: key "n" set to the number 3, and key "items" set '
         'to a list of three lowercase English words.',
         score_json),
        ("exactly_five_words",
         "Describe rain in exactly five words. No punctuation, no explanation.",
         score_five),
        ("code_is_prime",
         "Write a Python function is_prime(n) that returns True when n is prime. "
         "Reply with only one fenced code block containing the function.",
         score_code),
        ("needle",
         NEEDLE_LEAD + NEEDLE + NEEDLE_TAIL +
         "\n\nWhat was the custodian's access code? Answer with the code only.",
         lambda a, c: hit(a, r"azure\s*-\s*4471|azure4471", "Azure-4471")),
        ("count_letters",
         "How many times does the letter r appear in the word strawberry? Answer with the number only.",
         lambda a, c: hit(a, r"\b3\b(?!\s*[0-9])", "3")),
        ("no_invention",
         "In which year did the first crewed landing on the moon of the exoplanet Kepler-9d take place? "
         "Answer in one short sentence.",
         score_unknown),
        ("summary_20",
         SUMMARY_TEXT + "\n\nSummarise the passage in at most twenty words.",
         score_20_words),
    ]


# ---------------------------------------------------------------- scorers


def clean(answer):
    """The model's text with fences and stray markup removed, lowercased for comparison."""
    text = (answer or "").strip()
    text = re.sub(r"^```[a-zA-Z]*$", "", text, flags=re.M)
    text = text.replace("```", "")
    return text.strip()


def hit(answer, pattern, shown):
    ok = re.search(pattern, clean(answer).lower()) is not None
    return ok, ("found " + shown) if ok else ("no " + shown + " in: " + clean(answer)[:80])


def score_ball(answer, code=None):
    """The value in the answer's **first sentence** decides.

    The first version scanned the whole reply and rejected any mention of $0.10 - and qwen3:8b answers
    "The ball costs $0.05." then explains where $0.10 would come from, so a correct answer scored 0/3.
    A scorer that punishes the explanation for naming the wrong number is measuring its own bug.
    """
    text = clean(answer).lower()
    # a period only ends the sentence when whitespace follows it: "$0.05." must survive the split
    head = re.split(r"(?<=\.)\s+|\n", text, maxsplit=1)[0]
    if re.search(r"\$?\s*0?\.05|\b5\s*cents?\b", head) and not re.search(r"\b0\.10\b|\b10\s*cents?\b", head):
        return True, "0.05"
    return False, "expected 0.05, saw: " + head[:80]


def score_planets(answer, code=None):
    order = ["mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune"]
    text = clean(answer).lower()
    positions, last = [], -1
    for name in order:
        at = text.find(name)
        positions.append(at)
        if at <= last:
            return False, "out of order or missing at " + name
        last = at
    return True, "eight planets in order"


def score_json(answer, code=None):
    text = clean(answer)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        return False, "no JSON object"
    try:
        obj = json.loads(text[start:end + 1])
    except json.JSONDecodeError as error:
        return False, "unparsable: " + str(error)[:60]
    if obj.get("n") != 3:
        return False, "n is " + repr(obj.get("n"))
    items = obj.get("items")
    if not isinstance(items, list) or len(items) != 3:
        return False, "items is " + repr(items)[:60]
    if not all(isinstance(word, str) and word.isalpha() and word == word.lower() for word in items):
        return False, "items not three lowercase words: " + repr(items)[:60]
    return True, "valid shape"


def score_five(answer, code=None):
    words = [w for w in re.split(r"\s+", clean(answer)) if w]
    ok = len(words) == 5
    return ok, ("5 words" if ok else "%d words: %r" % (len(words), " ".join(words)[:60]))


def score_code(answer, code=None):
    """Execute the function. The tests are the verdict, not the look of the code."""
    body = answer or ""
    fence = re.search(r"```(?:python)?\s*(.*?)```", body, re.S)
    source = fence.group(1) if fence else body
    namespace = {}
    try:
        exec(compile(source, "<model>", "exec"), namespace)
    except Exception as error:  # noqa: BLE001 - any failure here is the model's
        return False, "code did not compile/run: " + str(error)[:70]
    fn = namespace.get("is_prime")
    if not callable(fn):
        return False, "no is_prime defined"
    cases = {2: True, 3: True, 4: False, 17: True, 25: False, 97: True, 1: False, 0: False, -7: False}
    for value, want in cases.items():
        try:
            got = bool(fn(value))
        except Exception as error:  # noqa: BLE001
            return False, "is_prime(%d) raised %s" % (value, error)
        if got != want:
            return False, "is_prime(%d) returned %s" % (value, got)
    return True, "all nine cases"


def score_unknown(answer, code=None):
    """A fact that cannot be known must be declined. An invented year is the failure."""
    text = clean(answer).lower()
    declined = any(word in text for word in
                   ("unknown", "not known", "no information", "cannot", "can't", "unable", "no such",
                    "does not exist", "fiction", "not a real", "no record", "never happened",
                    "did not occur", "didn't occur", "never occurred", "no crewed landing", "has not occurred",
                    "not a real place", "no evidence",
                    # qwen3.5:9b's phrasing: "There has never been a crewed landing on the moon of Kepler-9d"
                    "never been a", "has never been", "there has never"))
    invented = re.search(r"\b(1[89]\d\d|20\d\d)\b", text) is not None
    if declined and not invented:
        return True, "declined"
    if invented:
        return False, "invented a year: " + text[:80]
    return False, "neither declined nor dated: " + text[:80]


def score_20_words(answer, code=None):
    words = [w for w in re.split(r"\s+", clean(answer)) if w]
    ok = 0 < len(words) <= 20
    return ok, ("%d words" % len(words)) if ok else ("%d words (over 20 or empty)" % len(words))


# ---------------------------------------------------------------- transport


def chat(base_url, model, prompt, max_tokens, seed, temperature=0.0, timeout=300):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "seed": seed,
        "stream": False,
    }
    request = urllib.request.Request(
        base_url.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    started = time.time()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    elapsed = time.time() - started
    choice = (payload.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    return {
        "content": message.get("content") or "",
        "reasoning": message.get("reasoning_content") or message.get("reasoning") or "",
        "finish": choice.get("finish_reason"),
        "usage": payload.get("usage") or {},
        "seconds": round(elapsed, 2),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--model", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--max-tokens", type=int, default=640)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    rows = []
    for name, prompt, scorer in tasks():
        for run in range(args.runs):
            try:
                reply = chat(args.base_url, args.model, prompt, args.max_tokens, args.seed)
            except urllib.error.URLError as error:
                print("transport failure on %s run %d: %s" % (name, run + 1, error), file=sys.stderr)
                payload = {"content": "", "reasoning": "", "finish": "transport-error", "usage": {}, "seconds": 0}
            else:
                payload = reply
            ok, why = scorer(payload["content"], None)
            rows.append({
                "task": name, "run": run + 1, "ok": ok, "why": why,
                "finish": payload["finish"], "seconds": payload["seconds"],
                "content": payload["content"], "reasoning_chars": len(payload["reasoning"]),
            })
            print("%-20s run %d  %s  %-40s (%ss, finish=%s)" %
                  (name, run + 1, "pass" if ok else "FAIL", why[:40], payload["seconds"], payload["finish"]),
                  file=sys.stderr)

    per_task = {}
    for row in rows:
        per_task.setdefault(row["task"], []).append(1 if row["ok"] else 0)
    total = sum(sum(v) for v in per_task.values())
    possible = len(rows)
    summary = {
        "label": args.label,
        "model": args.model,
        "base_url": args.base_url,
        "runs": args.runs,
        "max_tokens": args.max_tokens,
        "temperature": 0.0,
        "seed": args.seed,
        "per_task": {k: v for k, v in per_task.items()},
        "passed": total,
        "possible": possible,
        "rate": round(total / possible, 3) if possible else 0.0,
        "rows": rows,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=1)
    print("\n%s (%s): %d/%d = %.1f%%" % (args.label, args.model, total, possible, 100 * summary["rate"]))
    for task, vector in per_task.items():
        print("  %-20s %s" % (task, vector))


if __name__ == "__main__":
    main()
