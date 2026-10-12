"""rescore.py - re-score stored reasoning replies with a declared answer-extraction rule.

Why: `knowledge_deep.py` scored the reasoning form by taking the FIRST `[ABCD]` token in the reply. Qwen3.6
often opens by echoing the option it is discussing ("A. 4:1  1. The decisive fact is ... D (9:4) is actually
the correct answer"), so the first token is the distractor it is about to reject. Three of the six
disagreements in the 93-item run were that artifact, all of them against the same model - i.e. the extractor
was measuring answer *formatting*, not knowledge. Strata opens every reply with "**Answer: X**", which the
rule catches.

Rule, applied in order, and the method is recorded so a reader can audit it:
  1. explicit  - an explicit answer phrase ("the answer is X", "answer: X", "correct answer is X");
  2. bare      - the first line that is only a letter (optionally with . or ));
  3. first     - the first standalone [ABCD] token (the original rule);
  4. ambiguous - an explicit phrase names a DIFFERENT letter than the rule picked.

No inference: this reads the stored replies in knowledge-deep-result-*-93.json.

Usage: python rescore.py [--labels qwen36-deep-93,strata-deep-93]
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPLICIT = re.compile(r'(?:the\s+)?(?:correct\s+)?answer(?:\s+is|\s*:)\s*\**\s*([ABCD])\b', re.I)
BARE = re.compile(r'^\s*\**\s*([ABCD])\s*[.)]?\s*\**\s*$')
ANY = re.compile(r'\b([ABCD])\b')


def parse_answer(reply):
    explicit = EXPLICIT.findall(reply)
    if explicit:
        return explicit[0].upper(), 'explicit'
    for line in reply.splitlines()[:3]:
        match = BARE.match(line.strip())
        if match:
            return match.group(1).upper(), 'bare'
    first = ANY.search(reply)
    if first:
        return first.group(1).upper(), 'first'
    return None, 'none'


def ambiguous(reply, picked):
    explicit = {l.upper() for l in EXPLICIT.findall(reply)}
    return bool(explicit) and picked not in explicit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--labels', default='qwen36-deep-93,strata-deep-93')
    args = parser.parse_args()
    for label in [l.strip() for l in args.labels.split(',')]:
        payload = json.loads((HERE / ('knowledge-deep-result-%s.json' % label)).read_text(encoding='ascii'))
        rows = payload['forms']['reason']['rows']
        methods, improved, worsened, ambig = {}, [], [], []
        naive_ok = rule_ok = 0
        for row in rows:
            naive = row['first_letter']
            letter, method = parse_answer(row['reply'])
            methods[method] = methods.get(method, 0) + 1
            naive_ok += 1 if naive == row['gold'] else 0
            rule_ok += 1 if letter == row['gold'] else 0
            if letter != naive:
                (improved if letter == row['gold'] else worsened).append((row['id'], naive, letter, row['gold'], method))
            if ambiguous(row['reply'], letter):
                ambig.append((row['id'], row['gold'], letter))
        n = len(rows)
        print('%-18s n=%d  first-letter %d/%d = %.1f%%   rule %d/%d = %.1f%%'
              % (label, n, naive_ok, n, 100 * naive_ok / n, rule_ok, n, 100 * rule_ok / n))
        print('   methods: %s' % methods)
        for item in improved:
            print('   FIXED   %s: first-letter said %s, rule says %s (gold %s, %s)' % item)
        for item in worsened:
            print('   BROKE   %s: first-letter said %s, rule says %s (gold %s, %s)' % item)
        for item in ambig:
            print('   AMBIGUOUS %s: rule picked %s, gold %s (reply names another letter explicitly)' % item)
        print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
