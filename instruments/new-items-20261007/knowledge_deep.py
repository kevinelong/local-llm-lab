"""knowledge_deep.py - expand the tied topic: reasoning, related facts, and a one-page paper.

Why: the MCQ instrument ties the two top stacks (88.5 % vs 89.7 %, inside one standard error), which says
they *recognise* the same things but nothing about whether they can *reason about* or *explain* them. This
extends the test on the topic they are most tied on - the shared-correct astronomy items, anchored on
**Mars**, the largest named-entity cluster in them - with three forms:

  1. `reason` - 8 held-out items both stacks got right: the answer, the decisive fact, and why the
     strongest distractor fails. Scored objectively where possible (letter, whether a distractor is
     addressed, whether the reply contradicts the gold).
  2. `facts`  - "list 25 checkable facts about Mars and its exploration". Verified against a PINNED
     Wikipedia corpus: coverage (are its content words traceable?) and numeric-claim accuracy.
  3. `paper`  - "a one-page paper (~550 words) on a related topic of your choice", topic on the first
     line, repeated at three seeds. Scored on length, topic-line validity, structure, and the same
     corpus checks.

Everything is local: the corpus is fetched once, hashed and pinned; no judge model is used. The
verifier is intentionally blunt - it can show coverage and numeric accuracy, and it cannot reliably
adjudicate "supported vs contradicted" prose. That limit is reported, not hidden.

Modes:
  python knowledge_deep.py --fetch                 fetch + pin the corpus
  python knowledge_deep.py --check                 offline self-test (gold vs negative responder)
  python knowledge_deep.py --url URL --model M --label L [--forms reason,facts,paper] [--seeds 3]
"""
import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import knowledge_run as kr                                   # reuse the responder + sampling helpers
from rescore import parse_answer                              # declared answer-extraction rule

CORPUS = HERE / 'knowledge-deep-corpus-20261010.json'
RESULTS = HERE / 'knowledge-deep-result-%s.json'
TOPIC_PAGES = ('Mars', 'Moons of Mars', 'Phobos (moon)', 'Deimos (moon)', 'Olympus Mons',
               'Valles Marineris', 'Atmosphere of Mars', 'Water on Mars', 'Exploration of Mars',
               'Mars rover', 'Geology of Mars', 'Climate of Mars')
EXTRACT_API = ('https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1'
               '&format=json&redirects=1&exlimit=max&titles=%s')
USER_AGENT = 'local-llm-lab/1.0 (offline benchmark corpus pinning; contact: local user)'
SEED = kr.SEED
TEMPERATURE = kr.TEMPERATURE

REASON_PROMPT = """/no_think
First line, exactly: ANSWER: <letter>
Then, in at most 120 words:
1. the single decisive fact for your answer,
2. why the strongest distractor is wrong.

Question: {question}
A. {a}
B. {b}
C. {c}
D. {d}"""

FACTS_PROMPT = """/no_think
List 25 checkable facts about Mars and its exploration, one per line, no numbering, no commentary.
Each fact must be a single sentence with at least one specific detail (a number, a name or a date)."""

PAPER_PROMPT = """/no_think
Write a one-page paper of about 550 words on a related topic of your choice within Mars science.
Put the topic on the first line by itself, then the paper. Take a position and support it."""


def _get_json(url, tries=4):
    for attempt in range(tries):
        request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 503) and attempt < tries - 1:
                wait = 5 * (attempt + 1)
                print('  %d from Wikipedia, waiting %ds' % (exc.code, wait))
                time.sleep(wait)
                continue
            raise
    raise RuntimeError('unreachable')


def fetch_corpus():
    titles = list(TOPIC_PAGES)
    pages = {}
    url = EXTRACT_API % urllib.request.quote('|'.join(titles))
    for page in (_get_json(url).get('query', {}).get('pages') or {}).values():
        text = (page.get('extract') or '').strip()
        if text:
            pages[page.get('title', '?')] = text
    print('batch of %d titles returned %d extracts' % (len(titles), len(pages)))
    have = {t.split(' (')[0].strip().lower() for t in pages}
    for title in titles:                                        # fill gaps one at a time, politely
        if title.split(' (')[0].strip().lower() in have:
            continue
        time.sleep(2.0)
        for page in (_get_json(EXTRACT_API % urllib.request.quote(title)).get('query', {}).get('pages') or {}).values():
            text = (page.get('extract') or '').strip()
            if text:
                pages[page.get('title', title)] = text
    corpus = {'fetched': '2026-10-10', 'source': 'en.wikipedia.org action=query prop=extracts explaintext',
              'anchor': 'Mars', 'pages': pages}
    body = json.dumps(corpus, sort_keys=True, ensure_ascii=True)
    corpus['sha256'] = hashlib.sha256(body.encode('utf-8')).hexdigest()
    CORPUS.write_text(json.dumps(corpus, ensure_ascii=True), encoding='ascii')
    total = sum(len(t.split()) for t in pages.values())
    print('corpus: %d pages, %d words, sha256 %s' % (len(pages), total, corpus['sha256'][:16]))
    return corpus


def load_corpus():
    """Corpus plus its evidence sets. `entities` are tokens the corpus itself capitalizes *inside* a
    sentence - i.e. genuine proper nouns/names, not the ordinary words that happen to start sentences.
    That distinction is what stops generic English from counting as grounded."""
    corpus = json.loads(CORPUS.read_text(encoding='ascii'))
    body = json.dumps({k: v for k, v in corpus.items() if k != 'sha256'}, sort_keys=True, ensure_ascii=True)
    assert hashlib.sha256(body.encode('utf-8')).hexdigest() == corpus['sha256'], 'corpus changed on disk'
    words, numbers, entities = set(), set(), set()
    for text in corpus['pages'].values():
        words |= {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z'\-]{2,}", text)}
        for token in re.findall(r'\d[\d,]*\.?\d*', text):
            numbers.add(token)
            numbers.add(re.sub(r'[^\d]', '', token))
        for sentence in re.split(r'(?<=[.!?])\s+', text):
            tokens = sentence.split()
            for token in tokens[1:]:                     # skip the sentence-initial capital
                bare = token.strip('(),;:\'"')
                if bare[:1].isupper() and len(bare) > 2 and bare.lower() not in STOP:
                    entities.add(bare.lower())
    return corpus, words, numbers, entities


NUMBER = re.compile(r'\d[\d,]*\.?\d*')
STOP = set("""a an the and or but if then than that this these those of in on at to for from with without by as is
are was were be been being it its their they them he she his her you your we our i not no nor so such very can
could may might must shall should will would do does did done have has had having there here where when which who
whom whose what why how all any both each few more most other some own same too also only just about into over
under again further once during before after above below up down out off between through because while until
against among within across per via s t d ll re ve m one two three four five first second new many much such
sentence fact facts line lines number numbered""".split())
SPECIFIC_LEN = 7


def content_tokens(text):
    return [w for w in re.findall(r"[A-Za-z][A-Za-z'\-]+", text) if w.lower() not in STOP and len(w) > 2]


def is_specific(token):
    """A token that carries information rather than general English: contains a digit, or is long."""
    return bool(re.search(r'\d', token)) or len(token) >= SPECIFIC_LEN


def figures(text):
    """Distinctive numeric claims only: 4+ digits or a real decimal. A trailing sentence period is
    stripped first - otherwise "in 4312." looks like a decimal and small integers sneak through."""
    out = []
    for raw in NUMBER.findall(text):
        value = raw.rstrip('.')
        if len(re.sub(r'[^\d]', '', value)) >= 4 or '.' in value:
            out.append(value)
    return out


def verify_text(text, words, numbers, entities):
    """Declared checks. `grounded` is the discriminator: the fraction of sentences naming at least one
    proper noun the corpus uses mid-sentence, or citing a figure that occurs in the corpus. It catches
    invented entities, vague generality and off-topic prose; it does NOT establish truth (a fact can
    name real entities and still be false) and it does not judge structure or argument. `vword_coverage`
    is reported for context only - it is close to "is this English", so it is not gated on."""
    sentences = [s for s in re.split(r'(?<=[.!?])\s+', text) if len(s.split()) > 3]
    content = content_tokens(text)
    traceable = sum(1 for w in content if w.lower() in words)
    grounded_sentences = 0
    for sentence in sentences:
        hit = any(t.lower() in entities for t in content_tokens(sentence))
        if not hit:
            hit = any(c in numbers or re.sub(r'[^\d]', '', c) in numbers for c in figures(sentence))
        grounded_sentences += 1 if hit else 0
    claims = figures(text)
    ok = sum(1 for value in claims if value in numbers or value.replace(',', '') in numbers
             or re.sub(r'[^\d]', '', value) in numbers)
    return {'words': len(text.split()), 'sentences': len(sentences),
            'vword_coverage': round(traceable / len(content), 3) if content else 0.0,
            'grounded': round(grounded_sentences / len(sentences), 3) if sentences else 0.0,
            'numeric_claims': len(claims), 'numeric_ok': ok,
            'numeric_rate': round(ok / len(claims), 3) if claims else None}


def shared_correct_astronomy():
    """Every astronomy item BOTH stacks answered correctly in the MCQ run - the recognition-tied pool.
    Read from the two result JSONs on disk, so the selection is the measured one, not a re-derivation."""
    failures = set()
    for name in ('knowledge-result-qwen36-131072.json', 'knowledge-result-strata-q2_0-65536.json'):
        payload = json.loads((HERE / name).read_text(encoding='ascii'))
        failures |= {f['id'] for f in payload['failures']}
    return [i for i in kr.load_items() if i['subject'] == 'astronomy' and i['id'] not in failures]


def reason_cases(limit=8, pool='mars'):
    """`mars`: the shared-correct items that mention Mars - the topic both stacks are tied on (the
    original selection). `shared`: every shared-correct astronomy item, in file order."""
    if pool == 'shared':
        return shared_correct_astronomy()[:limit]
    pool_items, seen = [], set()
    for item in kr.load_items():
        if item['subject'] != 'astronomy':
            continue
        blob = item['prompt'] + ' ' + ' '.join(item['choices'] or [])
        if 'Mars' in blob and item['id'] not in seen:
            pool_items.append(item)
            seen.add(item['id'])
    return pool_items[:limit]


def run(forms, responder, seeds, limit=8, pool='mars'):
    corpus, words, numbers, entities = load_corpus()
    out = {'responder': responder.name, 'anchor': corpus['anchor'], 'corpus_sha256': corpus['sha256'],
           'reason_prompt': REASON_PROMPT,
           'reason_pool': pool,
           'sampling': {'temperature': TEMPERATURE, 'seed': SEED, 'seeds_repeats': seeds}, 'forms': {}}
    if 'reason' in forms:
        rows = []
        for item in reason_cases(limit, pool):
            prompt = REASON_PROMPT.format(question=item['prompt'], a=item['choices'][0],
                                          b=item['choices'][1], c=item['choices'][2], d=item['choices'][3])
            reply = responder.answer(item, prompt)
            letters = re.findall(r'\b([ABCD])\b', reply.upper())
            naive = letters[0] if letters else None
            first, method = parse_answer(reply)
            others = [l for l in 'ABCD' if l != item['answer']]
            addressed = sum(1 for l in others if re.search(r'\b%s\b' % l, reply.upper()))
            rows.append({'id': item['id'], 'gold': item['answer'], 'first_letter': first, 'method': method,
                         'naive_letter': naive, 'naive_ok': naive == item['answer'],
                         'letter_ok': first == item['answer'],
                         'distractors_addressed': addressed,
                         'contradicts_gold': bool(first and first != item['answer'] and
                                                  re.search(r'\b%s\b is (correct|true|right)' % first, reply.lower())),
                         'words': len(reply.split()), 'reply': reply,
                         **verify_text(reply, words, numbers, entities)})
        out['forms']['reason'] = {
            'items': len(rows),
            'letter_correct': sum(1 for r in rows if r['letter_ok']),
            'mean_distractors_addressed': round(sum(r['distractors_addressed'] for r in rows) / max(1, len(rows)), 2),
            'rows': rows}
    if 'facts' in forms:
        item = {'suite': 'mmlu', 'id': 'facts', 'subject': 'astronomy', 'prompt': '', 'choices': None}
        reply = responder.answer(item, FACTS_PROMPT)
        lines = [l.strip(' -*\t') for l in reply.splitlines() if l.strip() and not l.strip().startswith('```')]
        facts = [l for l in lines if len(l) > 20]
        check = verify_text('\n'.join(facts), words, numbers, entities)
        per_fact = [dict(fact=f, **verify_text(f, words, numbers, entities)) for f in facts]
        out['forms']['facts'] = {'facts_listed': len(facts), **check,
                                 'facts_with_numbers': sum(1 for f in per_fact if f['numeric_claims']),
                                 'facts_ungrounded': sum(1 for f in per_fact if f['grounded'] == 0),
                                 'facts_grounded': sum(1 for f in per_fact if f['grounded'] > 0),
                                 'rows': per_fact}
    if 'paper' in forms:
        papers = []
        for index in range(seeds):
            item = {'suite': 'mmlu', 'id': 'paper-%d' % index, 'subject': 'astronomy',
                    'prompt': '', 'choices': None}
            reply = responder.answer(item, PAPER_PROMPT)
            lines = [l for l in reply.splitlines() if l.strip()]
            topic = lines[0].strip(' #*') if lines else ''
            papers.append({'seed_index': index, 'topic_line': topic[:120],
                           'topic_on_subject': any(k in topic for k in ('Mars', 'martian', 'Phobos',
                                                                       'Deimos', 'olympus', 'solar system')),
                           'paragraphs': len([l for l in lines if len(l.split()) > 25]),
                           **verify_text(reply, words, numbers, entities), 'reply': reply})
        out['forms']['paper'] = {'papers': len(papers), 'on_subject': sum(1 for p in papers if p['topic_on_subject']),
                                 'mean_words': round(sum(p['words'] for p in papers) / max(1, len(papers))),
                                 'grounded': round(sum(p['grounded'] for p in papers) / max(1, len(papers)), 3),
                                 'mean_vword_coverage': round(sum(p['vword_coverage'] for p in papers) / max(1, len(papers)), 3),
                                 'distinct_topics': len({p['topic_line'].lower() for p in papers}),
                                 'rows': papers}
    return out


class CorpusResponder:
    """Gold: answers from the pinned corpus - proves the verifier can see a fully traceable answer."""

    name = 'gold'

    def answer(self, item, prompt):
        corpus, _, _, _ = load_corpus()
        pages = corpus['pages']
        text = pages.get(corpus['anchor']) or pages[max(pages, key=lambda k: len(pages[k]))]
        if 'multiple-choice' in prompt or 'Question:' in prompt:
            return 'The answer is %s. Mars is the fourth planet from the Sun.\nA is wrong, B is wrong, C is wrong.' % item['answer']
        if 'List 25' in prompt:
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s) > 40][:25]
            return '\n'.join(sentences)
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s) > 40][:28]
        return 'Mars science: an assessment\n\n' + '\n\n'.join(' '.join(sentences[i:i + 4]) for i in range(0, 28, 4))


class OffTopicResponder:
    """Negative control: fluent prose with nothing to do with the corpus, and invented numbers."""

    name = 'offtopic'

    def answer(self, item, prompt):
        junk = ['Zorblax the Magnificent rules the seventh moon of Vex with an iron spreadsheet.',
                'The quantum turnip harvest reached 987654 units in the year 4312.',
                'Nothing in this sentence can be traced to any encyclopedia ever printed.']
        if 'Question:' in prompt:
            return 'The answer is %s.\n%s' % (item['answer'], ' '.join(junk))
        if 'List 25' in prompt:
            return '\n'.join('%s Fact number %d.' % (junk[i % 3], i) for i in range(25))
        return 'A thesis on Vex\n\n' + '\n\n'.join(' '.join(junk) for _ in range(4))


class GenericResponder:
    """Known weakness, asserted rather than hidden: fluent, generically true astronomy prose with no
    Mars specifics. The corpus checks should score this HIGH - they measure grounding, not truth or
    informativeness - so a high score here is the instrument behaving as documented."""

    name = 'generic'

    def answer(self, item, prompt):
        prose = ('The planets travel around the Sun on elliptical orbits, and gravity explains why they '
                 'remain bound to it. Telescopes observe the sky at many wavelengths, and spectroscopy '
                 'reveals the composition of distant objects. Stars form in clouds of gas and dust, and '
                 'they eventually exhaust their fuel. Careful measurement is what separates a scientific '
                 'claim from a guess.')
        if 'Question:' in prompt:
            return 'The answer is %s. %s' % (item['answer'], prose)
        if 'List 25' in prompt:
            parts = [p.strip() for p in prose.split('. ') if p.strip()]
            return '\n'.join(parts[i % len(parts)] + '. Observations constrain the model.' for i in range(25))
        return 'The value of careful measurement\n\n' + '\n\n'.join(prose for _ in range(4))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--url', default='http://127.0.0.1:11436')
    parser.add_argument('--model', default='local')
    parser.add_argument('--label', default='live')
    parser.add_argument('--forms', default='reason,facts,paper')
    parser.add_argument('--seeds', type=int, default=3)
    parser.add_argument('--limit', type=int, default=8)
    parser.add_argument('--pool', default='mars', choices=['mars', 'shared'])
    parser.add_argument('--timeout', type=int, default=300)
    args = parser.parse_args()

    if args.fetch or not CORPUS.exists():
        fetch_corpus()
        if args.fetch:
            return 0

    forms = [f.strip() for f in args.forms.split(',')]
    if args.check:
        gold = run(forms, CorpusResponder(), args.seeds)['forms']
        junk = run(forms, OffTopicResponder(), args.seeds)['forms']
        blur = run(forms, GenericResponder(), args.seeds)['forms']
        ok = True
        if 'reason' in forms:
            good = gold['reason']['letter_correct'] == gold['reason']['items']
            ok = ok and good
            print('gold letter-correct %d/%d  %s' % (gold['reason']['letter_correct'],
                                                     gold['reason']['items'], 'PASS' if good else 'FAIL'))
        if 'facts' in forms:
            g, j, b = gold['facts']['grounded'], junk['facts']['grounded'], blur['facts']['grounded']
            gn, jn = gold['facts']['numeric_rate'] or 0.0, junk['facts']['numeric_rate'] or 0.0
            good = g > 0.9 and j < 0.5 and gn >= 0.9 and jn <= 0.2
            ok = ok and good
            print('facts grounded: gold %.3f (want >0.9)  junk %.3f (want <0.5)  generic %.3f  |  '
                  'figures correct: gold %.2f (want >=0.9)  junk %.2f (want <=0.2)  %s'
                  % (g, j, b, gn, jn, 'PASS' if good else 'FAIL'))
        if 'paper' in forms:
            g = gold['paper']['rows'][0]['grounded']
            j = junk['paper']['rows'][0]['grounded']
            b = blur['paper']['rows'][0]['grounded']
            good = g > 0.9 and j < 0.5 and gold['paper']['on_subject'] == gold['paper']['papers']
            ok = ok and good
            print('paper grounded: gold %.3f (want >0.9)  junk %.3f (want <0.5)  generic %.3f  '
                  'on-subject %d/%d  %s' % (g, j, b, gold['paper']['on_subject'],
                                            gold['paper']['papers'], 'PASS' if good else 'FAIL'))
        print('LIMIT: grounding is coarse - the entity set legitimately contains domain nouns the corpus '
              'capitalizes mid-sentence (Moon, Sun, Earth), and generic-but-true prose can score high. '
              'The exact-figure check is the sharp one; truth and argument quality are not measured.')
        return 0 if ok else 1

    responder = kr.EngineResponder(args.url, args.model, args.timeout)
    result = run(forms, responder, args.seeds, limit=args.limit, pool=args.pool)
    target = Path(str(RESULTS) % args.label)
    target.write_text(json.dumps(result, indent=1), encoding='ascii')
    print('%-24s -> %s' % (args.model, target.name))
    if 'reason' in result['forms']:
        f = result['forms']['reason']
        print('  reason : letters %d/%d  mean distractors addressed %.2f'
              % (f['letter_correct'], f['items'], f['mean_distractors_addressed']))
    if 'facts' in result['forms']:
        f = result['forms']['facts']
        print('  facts  : %d listed, grounded %.3f, numeric %s, ungrounded %d'
              % (f['facts_listed'], f['grounded'], f['numeric_rate'], f['facts_ungrounded']))
    if 'paper' in result['forms']:
        f = result['forms']['paper']
        print('  paper  : %d papers, mean %d words, on-subject %d, distinct topics %d, grounded %.3f'
              % (f['papers'], f['mean_words'], f['on_subject'], f['distinct_topics'], f['grounded']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
