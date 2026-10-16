"""knowledge_run.py - run the pinned knowledge instrument against an engine, or self-test it offline.

The instrument: `knowledge-items-20261009.jsonl`, 1,100 pinned items - 800 MMLU (8 subjects, four-way
multiple choice) for factual recognition/recall, 300 GSM8K for the procedural control. The pair is the
point: low-bit quantisation damages factual recall far harder than step-by-step reasoning, so a model
that holds GSM8K while losing MMLU has the aggressive-quant signature rather than "less knowledge".

Sampling is pinned per request (temperature 0, fixed seed) because the running Strata config declares no
seed at all - a comparison across two stacks needs that control explicitly, not by default.

Modes:
  python knowledge_run.py --check
      Offline self-test. Renders every item's prompt, answers with a gold responder and a seeded random
      one, and scores both. The gold responder must score 100 % on both suites (that is what proves the
      prompt carries the answer and the parser reads it back) and the random responder must land near
      chance on MMLU. No engine, no GPU.

  python knowledge_run.py --url http://127.0.0.1:11436 --model qwen3.6-35b-a3b --label nine9
      Live run against an OpenAI-compatible endpoint (llama-server, Strata, Ollama). Writes
      knowledge-result-<label>.json and prints per-subject rates with n.

Usage notes: `--limit N` scores only the first N items per suite (cost control); `--timeout S` bounds
each request.
"""
import argparse
import json
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ITEMS = HERE / 'knowledge-items-20261009.jsonl'
SOURCES = HERE / 'knowledge-sources.json'
SEED = 20261009
TEMPERATURE = 0

# `/no_think` is the Qwen3-family switch (harmless text for others) and matters here: without it
# a reasoning model spends its whole answer allowance inside the thinking block - the same
# truncation the suite hit - and a preamble letter poisons the parser.
MCQ_PROMPT = """/no_think
Answer the multiple-choice question. Reply with one letter only: A, B, C or D.

Question: {question}
A. {a}
B. {b}
C. {c}
D. {d}

Answer:"""

MATH_PROMPT = """Solve the problem. End your reply with a final line in exactly this form:
#### <number>

Problem: {question}"""


def load_items():
    items = [json.loads(line) for line in ITEMS.read_text(encoding='ascii').splitlines() if line.strip()]
    pin = json.loads(SOURCES.read_text(encoding='ascii'))['items_sha256']
    import hashlib
    actual = hashlib.sha256(ITEMS.read_bytes()).hexdigest()
    assert actual == pin, 'instrument changed on disk: %s != %s' % (actual, pin)
    return items


def render(item):
    if item['suite'] == 'mmlu':
        choices = item['choices']
        return MCQ_PROMPT.format(question=item['prompt'], a=choices[0], b=choices[1],
                                 c=choices[2], d=choices[3]), '(A|B|C|D)'
    return MATH_PROMPT.format(question=item['prompt']), '####'


LETTER = re.compile(r'\b([ABCD])\b')
NUMBER = re.compile(r'-?\d[\d,]*\.?\d*')


def parse(item, reply):
    """Return the model's answer in the item's own vocabulary, or None if nothing parseable is present."""
    if item['suite'] == 'mmlu':
        matches = LETTER.findall(reply.upper())
        return matches[-1] if matches else None
    tail = reply.split('####')[-1] if '####' in reply else reply
    numbers = NUMBER.findall(tail.replace(',', ''))
    if not numbers:
        numbers = NUMBER.findall(reply.replace(',', ''))
    return numbers[-1].rstrip('.') if numbers else None


def as_number(text):
    """`2,125`, `$2,125` and `2125` are the same number - normalise both sides before comparing."""
    if text is None:
        return None
    cleaned = str(text).replace(',', '').replace('$', '').replace(' ', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def correct(item, reply):
    given = parse(item, reply)
    if given is None:
        return False, None
    if item['suite'] == 'mmlu':
        return given == item['answer'], given
    left, right = as_number(given), as_number(item['answer'])
    if left is not None and right is not None:
        return abs(left - right) < 1e-6, given
    return str(given).strip() == str(item['answer']).strip(), given


class GoldResponder:
    """Answers from the gold label - the check that the prompt carries the answer and the parser reads it."""

    name = 'gold'

    def answer(self, item, prompt):
        if item['suite'] == 'mmlu':
            return 'The answer is %s.' % item['answer']
        return 'Working it through.\n#### %s' % item['answer']


class RandomResponder:
    """Seeded guesser - should land near chance on MMLU and fail GSM8K."""

    name = 'random'

    def __init__(self, seed=SEED):
        self.random = random.Random(seed)

    def answer(self, item, prompt):
        if item['suite'] == 'mmlu':
            return self.random.choice(['A', 'B', 'C', 'D'])
        return '#### %d' % self.random.randint(1, 1000)


class EngineResponder:
    def __init__(self, url, model, timeout, max_tokens_mcq=512, max_tokens_math=1024):
        self.url = url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.max_mcq = max_tokens_mcq
        self.max_math = max_tokens_math
        self.name = model

    def answer(self, item, prompt):
        body = {
            'model': self.model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': TEMPERATURE,
            'seed': SEED,
            'stream': False,
            'max_tokens': self.max_mcq if item['suite'] == 'mmlu' else self.max_math,
            # Both engines otherwise let a reasoning block eat the whole allowance, which returns an
            # EMPTY content field - measured, twice: 0/6 then 2/6 with the answers never emitted. The
            # knobs are per request, so no pinned engine config is touched: llama.cpp reads the template
            # kwarg, the Strata engine reads reasoning_budget_tokens from the request body.
            'chat_template_kwargs': {'reasoning_effort': 'none'},
            'reasoning_budget_tokens': 0,
        }
        request = urllib.request.Request(
            self.url + '/v1/chat/completions', data=json.dumps(body).encode('utf-8'),
            headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            payload = json.load(response)
        message = payload['choices'][0]['message']
        # a reasoning engine may still emit only reasoning_content; never score an empty string as a wrong answer
        return message.get('content') or message.get('reasoning_content') or ''


def score(items, responder, verbose=False, checkpoint=None, every=25, carry=None, declared=None):
    """Score every item, optionally rewriting a partial result file as it goes.

    `checkpoint` is the path the finished result is written to; every `every` items the same JSON shape
    lands there with `partial: true`, so a run killed at the wall (or by a timeout) leaves the items it did
    finish rather than nothing. That is not hypothetical: on 2026-10-15 a 7,200 s Colibri run produced no
    artifact at all, because the file was only written after the last item.

    `carry` is an optional (per_subject, failures) pair from such a partial run: a resumed run adds to it
    instead of starting from zero, and `declared` names the full item count when only part is being run.
    """
    per_subject, failures = ({}, []) if carry is None else (carry[0], carry[1])
    started, done = time.monotonic(), sum(b.get('n', 0) for b in per_subject.values())
    declared_total = declared if declared is not None else done + len(items)

    def summary(partial):
        passed = sum(b['passed'] for b in per_subject.values())
        total = sum(b['n'] for b in per_subject.values())
        out = {'responder': responder.name, 'passed': passed, 'total': total,
               'rate': round(passed / total, 4) if total else None,
               'seconds': round(time.monotonic() - started, 1),
               'sampling': {'temperature': TEMPERATURE, 'seed': SEED},
               'per_subject': per_subject, 'failures': failures}
        if partial:
            out['partial'] = True
            out['scored_items'] = done
            out['declared_items'] = declared_total
        return out

    for item in items:
        prompt, _ = render(item)
        try:
            reply = responder.answer(item, prompt)
            ok, given = correct(item, reply)
        except Exception as error:            # a transport failure is not a model failure
            ok, given, reply = False, None, 'TRANSPORT: %r' % (error,)
        bucket = per_subject.setdefault(item['subject'], {'n': 0, 'passed': 0})
        bucket['n'] += 1
        bucket['passed'] += 1 if ok else 0
        if not ok:
            failures.append({'id': item['id'], 'expected': item['answer'], 'parsed': given,
                             'reply': reply[:200]})
        if verbose and not ok:
            print('  miss %-42s expected %-6s parsed %-6s | %s' % (
                item['id'], item['answer'], given, reply[:60].replace('\n', ' ')))
        done += 1
        if checkpoint is not None and every and done % every == 0 and done < declared_total:
            Path(checkpoint).write_text(json.dumps(summary(True), indent=1), encoding='ascii')
    return summary(False)


def resume_from(path, items):
    """(carry, remaining items, declared, skipped) read from a partial result at `path`.

    Items are scored in a stable file order, so a partial run's per-subject counts say exactly how many to
    skip: the first N of the same list. Returns carry=None when there is nothing to resume, so a fresh run is
    unaffected by the flag. Credit is carried, not re-earned: the counts and failures from the partial run
    seed the new accumulators, which is why the finished file is the same 1,100-item result either way.
    """
    path = Path(path)
    if not path.exists():
        return None, items, len(items), 0
    try:
        prior = json.loads(path.read_text(encoding='ascii'))
    except Exception:
        return None, items, len(items), 0
    if not prior.get('partial'):
        return None, items, len(items), 0
    counts = prior.get('per_subject') or {}
    skipped = sum(b.get('n', 0) for b in counts.values())
    if not skipped or skipped >= len(items):
        return None, items, len(items), 0
    return (counts, prior.get('failures') or []), items[skipped:], len(items), skipped


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='offline self-test, no engine')
    parser.add_argument('--url', default='http://127.0.0.1:11436')
    parser.add_argument('--model', default='local')
    parser.add_argument('--label', default='live')
    parser.add_argument('--limit', type=int, default=0, help='items per suite (0 = all)')
    parser.add_argument('--timeout', type=int, default=180)
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--resume', action='store_true',
                        help='continue a partial result for this label instead of starting over')
    args = parser.parse_args()

    items = load_items()
    if args.limit:
        kept, seen = [], {}
        for item in items:
            seen[item['suite']] = seen.get(item['suite'], 0)
            if seen[item['suite']] < args.limit:
                kept.append(item)
                seen[item['suite']] += 1
        items = kept
    print('instrument: %d items (%s)' % (len(items), ', '.join(
        '%s %d' % (s, sum(1 for i in items if i['suite'] == s)) for s in sorted({i['suite'] for i in items}))))

    if args.check:
        ok = True
        for responder in (GoldResponder(), RandomResponder()):
            result = score(items, responder, verbose=args.verbose)
            print('%-7s %4d/%-4d rate %.3f  (%.1fs)' % (responder.name, result['passed'], result['total'],
                                                        result['rate'], result['seconds']))
            for subject in sorted(result['per_subject']):
                bucket = result['per_subject'][subject]
                print('        %-34s %3d/%-4d' % (subject, bucket['passed'], bucket['n']))
            if responder.name == 'gold':
                gold_ok = result['rate'] == 1.0
                ok = ok and gold_ok
                print('        gold must be perfect (prompt carries the answer, parser reads it back):',
                      'PASS' if gold_ok else 'FAIL')
            else:
                mmlu = [b for s, b in result['per_subject'].items() if s != 'grade_school_math']
                chance = sum(b['passed'] for b in mmlu) / max(1, sum(b['n'] for b in mmlu))
                sane = 0.15 <= chance <= 0.40
                ok = ok and sane
                print('        random must sit near chance on MMLU (0.25 for four options):',
                      'PASS' if sane else 'FAIL', '(%.3f)' % chance)
        return 0 if ok else 1

    responder = EngineResponder(args.url, args.model, args.timeout)
    out = HERE / ('knowledge-result-%s.json' % args.label)
    # The result path doubles as the checkpoint: every 25 items a partial file (partial: true) is written
    # there, so a wall-clock kill leaves the finished items instead of nothing. With --resume that same
    # partial file is the base a restarted run continues from, so a pause costs the engine's warm cache but
    # not the items already scored.
    carry, declared, skipped = None, len(items), 0
    if args.resume:
        carry, items, declared, skipped = resume_from(out, items)
        if skipped:
            print('resuming %s: %d of %d items already scored, %d to go'
                  % (out.name, skipped, declared, len(items)))
    result = score(items, responder, verbose=args.verbose, checkpoint=out, carry=carry, declared=declared)
    if skipped:
        result['resumed_from'] = skipped
    # A run whose every reply is a transport error is UNSCORED, not a zero. On 2026-10-15 the Colibri item
    # named a model the engine does not serve (the engine advertises `qwen3.6-colibri`; the request said
    # `qwen36-35b`), so all 1,100 requests came back `404 model_not_found` in 13 s - and this script exited
    # 0 with a 0/1100 that read like a model verdict. Partial transport failure is worse than obvious,
    # because the items that *did* answer are the ones that ran before the engine died: the survivors are
    # positional, not a sample (the 2026-10-15 orphaned run scored 102/1100 that way, 989 of them
    # connection errors after the driver cleared the port under it). So ANY transport failure marks the
    # run unscored and exits nonzero; a usable result is one with no gap in it.
    transport = [f for f in result['failures'] if str(f.get('reply', '')).startswith('TRANSPORT:')]
    dead = bool(result['total']) and len(transport) == result['total']
    result['transport_failures'] = len(transport)
    result['scored'] = not transport
    out.write_text(json.dumps(result, indent=1), encoding='ascii')
    print('%-24s %4d/%-4d rate %.3f  (%.1fs)  -> %s' % (
        args.model, result['passed'], result['total'], result['rate'], result['seconds'], out.name))
    for subject in sorted(result['per_subject']):
        bucket = result['per_subject'][subject]
        print('        %-34s %3d/%-4d  %.3f' % (subject, bucket['passed'], bucket['n'],
                                                bucket['passed'] / bucket['n']))
    if transport:
        print('        %d of %d replies failed at the transport level, e.g. %s'
              % (len(transport), result['total'], transport[0]['reply']))
        print('        UNSCORED: %s - the items that answered are positional, not a sample'
              % ('every reply failed' if dead else 'the run has a gap in it'))
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
