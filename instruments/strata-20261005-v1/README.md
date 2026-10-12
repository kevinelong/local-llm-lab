# strata-20261005-v1: the OMP coding screen driven against Strata

First live run of the Strata engine (Qwen3.8-Flash-Next Coder IQ1_M) on this PC, driven by
the lab's OMP coding screen. Read `FLAGS.md` for the flag research and the chosen set, and
`REPORT.md` for results.

## What Strata is, and why the runner had to change

Strata is not a runtime this harness launches like llama-server. It is an install that
manages its own process: `setup.py` writes `strata-coder-iq1_m.json` and
`run-coder-iq1_m.bat`, and that launcher starts `serve/server.py --engine strata --config
<cfg> --port 8080`, which loads the model and serves OpenAI `/v1` (plus Anthropic
`/v1/messages`). The 2026-09-30 staging record therefore required a runner revision that
skips the llama-server launch and points the relay at Strata's endpoint.

`run.py` here does exactly that and reuses everything else:

- the Windows-Job spawn, memory/paging monitor, floors (3/2/0.5 GiB) and STOP support from
  the lab monitor;
- the OMP 18.3.1 harness invocation, token-budget relay and artifact scorer from
  `mimo-harness-20260925-v1` (`lab.execute`, `lab.configuration`), with `base.BASE` pointed
  at `http://127.0.0.1:8080` instead of a local llama-server;
- the staged task set from `completion-20260923-v1/source/staged_tasks_20260922.py`.

Actions:

```
python run.py check                 # setup.py --check: hardware verdict, installs nothing
python run.py install               # install with the chosen flags, then declare sampling
python run.py calibrate             # setup.py --calibrate: machine-measured engine settings
python run.py probe                 # start Strata, verify the endpoint, sampling and tool calls
python run.py screen events|ledger|paths   # one OMP session per task, Strata started and stopped
python run.py audit
```

Each session is bracketed by Strata's own start and stop, as the staging record requires.
Evidence lands in `evidence/` (`check.txt`, `install.txt`, `config.json`, `calibrate.txt`)
and in `probe/`, `runs/<task>/`.

## Declared configuration

Context 32768, `--kv int8`, Coder IQ1_M, vision off, low-RAM variant as setup chose it
(`--resident-experts`), `--draft-vocab en`, sampling temperature 1.0 / top_p 0.95 / min_p 0
/ top_k 64 (the server clamps top_k to 1..64, so the lab's top_k 0 cannot be expressed; the
deviation is declared in `FLAGS.md` and in the evidence). No `reasoning_budget_tokens` cap,
so thinking is the model's own, as in the MiMo runs.

## Gates

Unchanged: initial RAM >= 9 GiB and commit >= 8 GiB before a start; floors 3 / 2 / 0.5 GiB;
sustained-paging guard; STOP; one inference workload at a time; Windows Jobs; no reboot; no
app kills. The coding screen keeps the 720 s wall and the mimo-harness token budget
(`base.Budget(quota=16000, cap=12288)`, constructed inside `lab.execute`), so the numbers
sit next to the MiMo and new-harness runs. Strata is disk-bound on a 12 GB card, so a
timeout here is a platform finding, not a model verdict.

## Boundaries

Preserve every attempt in its own folder. Nothing is promoted; Strata is an external engine
under the MIT licence and the Coder weights are the Qwen Community Licence 1.0 (local
evaluation only). No second agent, no concurrent inference, no gate change.
