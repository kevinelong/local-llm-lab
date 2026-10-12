# instruments

A curated snapshot of this lab's measurement instruments, frozen inputs and small evidence, taken from
`C:/Users/kevin/ai_bench`. That directory is where the work actually lives, but it also holds tens of
gigabytes of model packs, run logs and wire captures, so it is not itself version-controlled; this is the
part of it that belongs in a public repository.

Everything here is copied by `refresh-snapshot.py`, which also writes `SNAPSHOT.json` - a map from every
copied file to its source path, size and sha256. To refresh after a change:

```
python instruments/refresh-snapshot.py     # add --check to report drift without writing
```

and commit the difference. The source directories, not this copy, are authoritative: the snapshot exists so
that someone reading the notes can see the code and the frozen inputs that produced the numbers, and so the
notes' relative links resolve.

## What is in here

| directory | what it is |
|---|---|
| `new-items-20261007/` | the knowledge instruments: `knowledge_run.py` (1,100 pinned MMLU+GSM8K items), `knowledge_deep.py` (the tied-topic expansion: reasoning, fact lists, papers, against a pinned Wikipedia corpus), `rescore.py` (the declared answer-extraction rule and the parse lesson), `deep_report.py`, `knowledge_ab.py` (the two-stack driver) |
| `bespoke-metric-20261010/` | the decision-suite metric work: `recompute.py` (re-derivation from frozen rows), `paired.py` (McNemar and bootstrap on the same records), `suite_report.py` (balanced accuracy, prediction rate, majority baseline, per family) |
| `colibri-laya-20261011/` | the Laya replay on a second engine: `laya_replay.py` over the 18 frozen decision windows, both question shapes |
| `decision-signal-20261011/` | `rule_vs_models.py`: the deterministic stall rules, scored against every neural decision model this lab has screened |
| `strata-warmcache-20261011/` | the warm-cache experiment on our own engine, cold versus warm at a fixed resident budget |
| `overnight-20261011/` | the overnight queue: `queue.json` (items with their pre-recorded predictions), `runner.py` (serial driver with gates and a STOP file), `items.py`, `shared.py`, `supervise.py`, `morning_report.py`, and the per-item logs |
| `bespoke-suite-20261010-v1/` | the platform-consistency re-run of the decision suite, including the per-record `rows.jsonl` evidence (7,760 records that matched the pre-upgrade run exactly) |
| `local-decisions-followup-20260925-v1/` | the frozen decision inputs and labels: `natural-inputs.json`, `natural-labels.json`, `protocol.json` (with the sha256 that pins them) and the question set |
| `strata-20261005-v1/` | the Strata run notes: `REPORT.md`, `FLAGS.md` and the small diagnostics |

## What is never in here

Model packs and weights of any kind (`.gguf`, `.safetensors`, `.bin`), archives and executables, databases,
wire captures, per-run logs and caches, `__pycache__`, and any single file over 2 MiB. The rule is checked by
the script rather than trusted: it reports what it skipped for size, and `SNAPSHOT.json` records exactly what
was taken.

Before every commit to this repository - it is public - the snapshot is scanned for API keys and tokens.
Nothing has ever been found; the scan is not optional.
