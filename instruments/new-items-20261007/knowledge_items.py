"""knowledge_items.py - fetch and pin a knowledge/recall instrument (2026-10-09).

Why: the lab has no factual-knowledge battery, so "does Qwen3.8-Flash-Next Q2_0 know more than
Qwen3.6-35B-A3B?" cannot be answered from any existing evidence (all nine batteries are procedural
coding/repair). This builds the instrument, with both forms that matter:

  * RECOGNITION/RECALL of facts - MMLU (multiple choice, 57 subjects), pulled per subject so the
    granularity is real rather than an aggregate.
  * PROCEDURAL control - GSM8K (grade-school math, free-form answer), because low-bit quantisation
    damages factual recall much harder than it damages step-by-step reasoning. A model that holds
    GSM8K while losing MMLU has the classic aggressive-quant signature, and that separates the two
    hypotheses (thinner weights vs thinner knowledge).

Sources are pinned by sha256 in `knowledge-sources.json`; the item file is written once and read-only
after that. Fetching needs network; scoring does not.

Usage: python knowledge_items.py            # fetch if missing, then report
       python knowledge_items.py --verify   # only re-hash what is on disk
"""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ITEMS = HERE / 'knowledge-items-20261009.jsonl'
SOURCES = HERE / 'knowledge-sources.json'

MMLU_SUBJECTS = ('high_school_world_history', 'high_school_geography', 'astronomy', 'world_religions',
                 'philosophy', 'prehistory', 'virology', 'international_law')
MMLU_PER_SUBJECT = 100
GSM8K_ITEMS = 300
# NB: the dataset name must stay percent-encoded, so the template is filled with .format(), not %.
ROWS_API = ('https://datasets-server.huggingface.co/rows?dataset=cais%2Fmmlu'
            '&config={config}&split=test&offset=0&length={length}')
GSM8K_URL = ('https://raw.githubusercontent.com/openai/grade-school-math/master/'
             'grade_school_math/data/test.jsonl')


def get(url, timeout=60):
    request = urllib.request.Request(url, headers={'User-Agent': 'local-llm-lab/1.0'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def mmlu_items():
    for subject in MMLU_SUBJECTS:
        payload = json.loads(get(ROWS_API.format(config=subject, length=MMLU_PER_SUBJECT)))
        for row in payload['rows']:
            item = row['row']
            yield {
                'id': 'mmlu/%s/%d' % (subject, row['row_idx']),
                'suite': 'mmlu',
                'subject': subject,
                'prompt': item['question'],
                'choices': list(item['choices']),
                'answer': 'ABCD'[item['answer']],
            }


def gsm8k_items():
    for index, line in enumerate(get(GSM8K_URL).decode('utf-8').splitlines()):
        if index >= GSM8K_ITEMS:
            break
        item = json.loads(line)
        yield {
            'id': 'gsm8k/%d' % index,
            'suite': 'gsm8k',
            'subject': 'grade_school_math',
            'prompt': item['question'],
            'choices': None,
            'answer': item['answer'].split('####')[-1].strip(),
        }


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    verify_only = '--verify' in sys.argv
    if not ITEMS.exists() and not verify_only:
        rows = list(mmlu_items()) + list(gsm8k_items())
        ITEMS.write_text('\n'.join(json.dumps(r, ensure_ascii=True) for r in rows) + '\n', encoding='ascii')
        SOURCES.write_text(json.dumps({
            'built': '2026-10-09',
            'reason': 'no factual-knowledge instrument existed in the lab; answers the Qwen3.8-Q2_0 vs '
                      'Qwen3.6 knowledge question with a recognition form (MMLU) and a procedural control (GSM8K)',
            'items_sha256': digest(ITEMS.read_bytes()),
            'mmlu': {'api': 'https://datasets-server.huggingface.co/rows (cais/mmlu, split=test)',
                     'subjects': list(MMLU_SUBJECTS), 'per_subject': MMLU_PER_SUBJECT},
            'gsm8k': {'url': GSM8K_URL, 'items': GSM8K_ITEMS},
        }, indent=1), encoding='ascii')
    rows = [json.loads(line) for line in ITEMS.read_text(encoding='ascii').splitlines() if line.strip()]
    suites = {}
    for row in rows:
        suites.setdefault(row['suite'], {}).setdefault(row['subject'], 0)
        suites[row['suite']][row['subject']] += 1
    print('items on disk:', len(rows))
    for suite, subjects in suites.items():
        print('  %-7s %d subject(s), %d items' % (suite, len(subjects), sum(subjects.values())))
    pin = json.loads(SOURCES.read_text(encoding='ascii')) if SOURCES.exists() else {}
    actual = digest(ITEMS.read_bytes())
    print('items sha256  :', actual[:16], '...')
    print('matches pin   :', actual == pin.get('items_sha256'), '(pin %s...)' % str(pin.get('items_sha256'))[:16])
    return 0 if actual == pin.get('items_sha256') else 1


if __name__ == '__main__':
    sys.exit(main())
