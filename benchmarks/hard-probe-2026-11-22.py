"""Harder suites: RULER-style long context, and BBH/GSM8K discrete reasoning.

Why these and not another ten hand-written prompts: the ten-task battery in `quality-pass-2026-11-22.py` is
saturated - four of five models scored 27/30 or better, which means it cannot rank them. The literature is
consistent about what does rank models of different sizes and, especially, different effective context:

  * **RULER** (Hsieh et al., 2024) - single-needle retrieval is saturated long before a model's advertised
    window; the probes that still separate models are *multi-needle*, *aggregation* (count a token in the
    haystack) and *variable tracking*. That is what `--suite longctx` implements, generated deterministically.
  * **BBH** (Suzgun et al., 2022) - compositional reasoning tasks where small models fail outright and the
    failure is not a wording artefact: date understanding, seven-object logical deduction.
  * **GSM8K** (Cobbe et al., 2021) - grade-school multi-step arithmetic, the classic size discriminator.

Every item is scored mechanically against the dataset's own answer; nothing here asks a model to grade.

  python benchmarks/hard-probe-2026-11-22.py --suite reasoning --base-url ... --model ... --limit 15
  python benchmarks/hard-probe-2026-11-22.py --suite longctx --ctx 32768 --base-url ... --model ...
"""

import argparse
import json
import pathlib
import random
import re
import sys
import time
import urllib.request

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"

# ------------------------------------------------------------------ long context


FILLER = [
    "The harbour office keeps its ledgers in a room above the chandlery, where the light is poor and the "
    "shelves are deeper than they look.",
    "Fishing boats return on the tide and unload in the order they arrive, which the clerk records in a book "
    "with a broken spine.",
    "The council meets on the first Tuesday of the month unless the weather closes the road, in which case it "
    "meets the following week.",
    "A lighthouse is only as good as its keeper's patience, and the keeper's patience is only as good as the "
    "supply boat.",
    "Old charts in the archive show a sandbar that no longer exists, and a channel that has since silted.",
    "The school on the hill takes children from four villages and closes early when the ferry is cancelled.",
    "Wind from the south-west brings rain within the hour, which every fisherman knows and no forecast repeats.",
    "The pier was rebuilt twice: once in timber after the gale, and once in stone after the council changed its "
    "mind.",
    "A ledger entry from 1974 records a crate of oranges that was never claimed and, by custom, was eaten.",
    "Nobody has counted the gulls since the count was abandoned, but everyone agrees there are fewer.",
]


def vt_tasks(ctx_tokens, reps, base_seed=500):
    """`reps` **distinct** variable-tracking chains, each with its own seed for both the chain and the filler.

    Repeating the same prompt at temperature 0 would mostly re-measure determinism; what needs measuring is whether a
    model can hold a twelve-assignment chain at this window at all. Each rep is therefore a different chain.
    """
    tasks = []
    for rep in range(reps):
        seed = base_seed + rep * 7
        rng = random.Random(seed)
        names = ["alpha", "beta", "gamma", "delta"]
        steps, state, last = [], {n: None for n in names}, None
        for _ in range(12):
            name = rng.choice(names)
            if rng.random() < 0.55:
                value = rng.choice([2, 4, 5, 6, 8, 9])
                state[name] = value
                steps.append("The variable %s is set to %d." % (name, value))
            else:
                source = rng.choice(names)
                state[name] = state[source]
                steps.append("The variable %s is assigned the value of %s." % (name, source))
            last = name
        # A chain can end on a variable that was only ever assigned *from* an unset one; asking its value would be
        # an unanswerable question, and the probe would be measuring the generator. Close the chain with a set.
        if state[last] is None:
            state[last] = rng.choice([2, 4, 5, 6, 8, 9])
            steps.append("The variable %s is set to %d." % (last, state[last]))
        want = state[last]
        # ONE haystack for every rep, so the repeats differ in the chain and not in a cold prefill: at 32K this
        # model processes a 16k prompt at 15-29 tok/s, so a fresh haystack per rep would cost ~20 minutes each and
        # measure the engine's prefill curve rather than the chain.
        sentences, _ = haystack(int(ctx_tokens * 0.60 * 3.4 / 5.8), seed=base_seed + 1)
        at = int(len(sentences) * 0.45)
        body = sentences[:at] + steps + sentences[at:]
        tasks.append(("variable_tracking#%d" % (rep + 1),
                      "\n".join(body) + "\n\nQuestion: At the end of the text, what is the value of the variable %s? "
                      "Answer with the number only." % last,
                      (lambda a, w=want: re.search(r"\b%d\b" % w, a) is not None), str(want)))
    return tasks


def haystack(target_words, seed=7):
    """Deterministic filler of roughly `target_words` words, made of distinct sentences in shuffled order."""
    rng = random.Random(seed)
    words = []
    sentences = []
    while len(words) < target_words:
        block = rng.sample(FILLER, len(FILLER))
        for sentence in block:
            words.extend(sentence.split())
            sentences.append(sentence)
            if len(words) >= target_words:
                break
    return sentences, words


def words_of(sentences):
    return sum(len(s.split()) for s in sentences)


def longctx_tasks(ctx_tokens, reps=1):
    """RULER-style probes, `reps` **distinct instances each** over one shared haystack.

    The repeats have to differ in what is asked, not in how long the preamble is: a fresh haystack at a 32K window
    costs a full prefill per repeat (15-29 tok/s past 10k on this model), which would measure the engine's prefill
    curve instead of the capability. So the filler is generated once and the needles - their text, value and depth -
    are what changes between reps, with the expected answers computed here.
    """
    target_words = int(ctx_tokens * 0.60 * 3.4 / 5.8)
    tasks = []

    for rep in range(1, reps + 1):
        rng = random.Random(1000 + rep)

        # 1. single needle at a per-rep depth
        sentences, _ = haystack(target_words, seed=7)
        code = 4000 + rng.randrange(900, 999)
        at = int(len(sentences) * (0.38 + 0.08 * rep))
        body = sentences[:at] + ["The spare gasket for the north pier is kept in locker %d." % code] + sentences[at:]
        tasks.append(("niah_single#%d" % rep, "\n".join(body) +
                      "\n\nQuestion: In which locker is the spare gasket for the north pier kept? "
                      "Answer with the locker number only.",
                      (lambda a, w=code: re.search(r"\b%d\b" % w, a) is not None), str(code)))

        # 2. four needles, values and depths per rep
        sentences, _ = haystack(target_words, seed=11)
        notes = ["the blue bell rings at 06:%02d" % rng.randrange(10, 59),
                 "the west gate is repainted %d" % (1900 + rng.randrange(10, 99)),
                 "the ferry timetable is signed %s" % rng.choice(["Okafor", "Kwon", "Adeyemi", "Lindqvist"]),
                 "the tide table is revised %s" % rng.choice(["Kwon", "Okafor", "Bergman", "Sato"])]
        marks = [int(len(sentences) * (0.15 + 0.2 * i)) for i in range(4)]
        body = []
        for i, sentence in enumerate(sentences):
            if i in marks:
                body.append("Record note: " + notes[marks.index(i)] + ".")
            body.append(sentence)
        tasks.append(("niah_multi#%d" % rep, "\n".join(body) +
                      "\n\nQuestion: List the four record notes exactly as written, one per line, nothing else.",
                      (lambda a, f=notes: all(all(w in a.lower() for w in phrase.split()[:4]) for phrase in f)),
                      "four record notes"))

        # 3. aggregation: count is per rep, and the marker never appears in the question
        sentences, _ = haystack(target_words, seed=13)
        count = [7, 5, 9][(rep - 1) % 3]
        marker = "narwhal"
        spots = random.Random(17 + rep).sample(range(len(sentences)), count)
        filled = ["A %s was recorded in the log." % marker if i in spots else s for i, s in enumerate(sentences)]
        tasks.append(("aggregation#%d" % rep, "\n".join(filled) +
                      "\n\nQuestion: in the passage above, and not counting this question, how many times does the "
                      "word \"%s\" appear? Answer with the number only." % marker,
                      (lambda a, w=count: re.search(r"\b%d\b" % w, a) is not None), str(count)))

        # 4. variable tracking, one chain per rep (the suite that survived repetition this morning)
        for name, prompt, scorer, want in vt_tasks(ctx_tokens, 1, base_seed=500 + rep * 3):
            tasks.append(("variable_tracking#%d" % rep, prompt, scorer, want))

    return tasks


# ------------------------------------------------------------------ reasoning


def bbh_options(prompt):
    """The multiple-choice options a BBH prompt lists, by letter: the target is a letter, but a model that
    answers the *value* (a date, an object) is right too, and comparing "12/25/1937" to "(B)" scored it wrong."""
    found = {}
    for match in re.finditer(r"^\(([A-G])\)\s*(.+)$", prompt, re.M):
        found[match.group(1)] = match.group(2).strip()
    return found


def letter_of(text):
    found = re.findall(r"ANSWER:\s*\(?([A-G])\)?", text, re.I)
    return found[-1].upper() if found else ""


def bbh_items(name, limit):
    document = json.loads((DATA / ("bbh-%s.json" % name)).read_text(encoding="utf-8"))
    items = []
    for example in document["examples"][:limit]:
        want = example["target"]
        options = bbh_options(example["input"])
        items.append((("bbh_%s" % name), example["input"], want, options.get(want.strip("()"), "")))
    return items


def bbh_ok(content, want, option_text):
    """Right if the model names the letter, or names the thing the letter stands for."""
    letter = letter_of(content)
    if letter == want.strip("()"):
        return True
    if option_text:
        tail = normalize_answer(content)
        if tail and normalize_answer(option_text) and normalize_answer(option_text) in tail:
            return True
    return False


def gsm8k_items(limit):
    path = DATA / "gsm8k-test.jsonl"
    items = []
    for line in path.read_text(encoding="utf-8").splitlines()[:limit]:
        row = json.loads(line)
        answer = row["answer"].split("####")[-1].strip().replace(",", "")
        items.append(("gsm8k", row["question"], answer,
                      lambda a, want=answer: numeric_answer(a) == want))
    return items


def normalize_answer(text):
    found = re.findall(r"ANSWER:\s*(.+)", text, re.I)
    candidate = found[-1] if found else text
    return re.sub(r"[^a-z0-9().]", "", candidate.lower())


def numeric_answer(text):
    found = re.findall(r"ANSWER:\s*\$?\s*(-?[\d,]+(?:\.\d+)?)", text, re.I)
    if found:
        return found[-1].replace(",", "")
    numbers = re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
    return numbers[-1] if numbers else ""


# ------------------------------------------------------------------ transport


def ask(base_url, model, prompt, max_tokens, num_ctx=0, timeout=1800):
    """Ollama's OpenAI endpoint cannot set the window, and a 14B served at 32,768 pays a 38 % CPU spill even for a
    two-hundred-token reasoning item (measured: 19 tok/s at 32K, 62 at 8K). So when a window is asked for and the
    server is Ollama, go through `/api/chat`, which takes `num_ctx`; otherwise use the OpenAI shape."""
    base = base_url.rstrip("/")
    if num_ctx and ":11434" in base:
        body = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False,
                "options": {"temperature": 0, "num_predict": max_tokens, "num_ctx": num_ctx}}
        request = urllib.request.Request(base + "/api/chat",
                                         data=json.dumps(body).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
        started = time.time()
        with urllib.request.urlopen(request, timeout=timeout) as response:
            reply = json.loads(response.read().decode("utf-8"))
        payload = {"choices": [{"message": {"content": reply.get("message", {}).get("content") or ""},
                                 "finish_reason": {"stop": "stop"}.get(reply.get("done_reason"), reply.get("done_reason"))}]}
        return payload, time.time() - started

    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "temperature": 0, "max_tokens": max_tokens, "stream": False}
    request = urllib.request.Request(base + "/v1/chat/completions",
                                     data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
    started = time.time()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload, time.time() - started


REASONING_PREFIX = ("Work the problem out, then put the final answer alone on the last line as "
                    "\"ANSWER: <value>\".\n\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=["longctx", "reasoning", "vt"], required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--ctx", type=int, default=32768, help="window for the long-context suite")
    parser.add_argument("--limit", type=int, default=15)
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--only", default="", help="comma-separated task names")
    parser.add_argument("--num-ctx", type=int, default=0, help="Ollama window; 0 = server default")
    parser.add_argument("--reps", type=int, default=5, help="vt: how many distinct chains")
    args = parser.parse_args()

    if args.suite == "longctx":
        plan = [(name, prompt, scorer, want, "") for name, prompt, scorer, want in longctx_tasks(args.ctx, args.reps)]
    elif args.suite == "vt":
        plan = [(name, prompt, scorer, want, "") for name, prompt, scorer, want in vt_tasks(args.ctx, args.reps)]
    else:
        plan = [(name, REASONING_PREFIX + prompt,
                 (lambda a, w=want, o=option: bbh_ok(a, w, o)), want, option)
                for name, prompt, want, option in bbh_items("date_understanding", args.limit)]
        plan += [(name, REASONING_PREFIX + prompt,
                  (lambda a, w=want, o=option: bbh_ok(a, w, o)), want, option)
                 for name, prompt, want, option in bbh_items("logical_deduction_seven_objects", args.limit)]
        plan += [(name, REASONING_PREFIX + prompt, scorer, want, "")
                 for name, prompt, want, scorer in gsm8k_items(args.limit)]

    if args.only:
        wanted = {n.strip() for n in args.only.split(",")}
        # match on the task name, so `--only aggregation` also selects `aggregation#1..#3`
        plan = [item for item in plan if item[0].split("#")[0] in wanted]

    rows = []
    for name, prompt, scorer, want, want_text in plan:
        try:
            payload, seconds = ask(args.base_url, args.model, prompt, args.max_tokens, args.num_ctx)
        except Exception as error:  # noqa: BLE001 - a transport failure is recorded, not hidden
            rows.append({"task": name, "ok": False, "why": "transport: " + str(error)[:80],
                         "want": str(want), "want_text": want_text, "prompt": prompt,
                         "content": "", "finish": "transport-error",
                         "seconds": 0, "prompt_chars": len(prompt)})
            print("%-28s FAIL transport %s" % (name, error), file=sys.stderr)
            continue
        choice = (payload.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        content = message.get("content") or ""
        ok = bool(scorer(content))
        # Everything, uncut: the reply and the prompt. Kevin's rule of 2026-11-23 - disk is cheaper than a
        # re-run, and a future reanalysis needs to see exactly what the model was asked, not a 2,000-char slice.
        rows.append({"task": name, "ok": ok, "why": "match" if ok else "no match",
                     "want": str(want), "want_text": want_text,
                     "prompt": prompt, "content": content,
                     "finish": choice.get("finish_reason"),
                     "seconds": round(seconds, 1), "prompt_chars": len(prompt)})
        print("%-28s %s  want=%-18s got=%r" % (name, "pass" if ok else "FAIL", str(want)[:18], content[-60:]),
              file=sys.stderr)

    per = {}
    for row in rows:
        per.setdefault(row["task"], []).append(1 if row["ok"] else 0)
    passed = sum(sum(v) for v in per.values())
    summary = {"label": args.label, "model": args.model, "suite": args.suite, "ctx": args.ctx,
               "per_task": per, "passed": passed, "possible": len(rows),
               "rate": round(passed / len(rows), 3) if rows else 0, "rows": rows}
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.out).write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print("\n%s %s: %d/%d" % (args.label, args.suite, passed, len(rows)))
    for task, vector in per.items():
        print("  %-30s %s" % (task, vector))


if __name__ == "__main__":
    main()
