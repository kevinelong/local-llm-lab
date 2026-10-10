# Plan items 2, 5, 7, 8: convention, engine decision, owner decisions, hygiene (2026-10-07)

Companion to the pre-registered plan (`my-plan-20261007-pre-registered.txt`). Items 1, 3, 4 and 6
are runs and are recorded in their own roots; this file covers the parts that are decisions or
conventions.

## Item 2 - reporting convention, adopted from today

Single runs on these harnesses are NOT point estimates, and the evidence is now specific rather than
general:

- MiniCPM5-2B `paths` scored 75/75, 75/75 and 9/75 under identical declared settings (and 220/221,
  218/221, 148/221 overall across four scored runs).
- Strata's Coder IQ1_M ledger split 70/70, 70/70, 64/70, 7/70, 7/70 - same declaration.
- Swift's `events` 76/76 and `ledger` 70/70 reproduced exactly two days apart, so the instability is
  task- and model-specific, not a blanket property.
- gpt-oss-20b's own plan (asked cold, no plan given) put reproducibility first for the same reason.

Convention from now on:
1. Every scored claim states n, and where n > 1 states the distribution, not just the best sample.
2. A configuration is only ranked once it has n >= 3, or the row is explicitly labelled "n=1 sample".
3. When a "best observed" number is quoted (as the ranking tables do), the selection rule is stated in
   the same table's caption.
4. Tasks are reported separately: a model can be stable on `events`/`paths` and unstable on `ledger`.
5. Rates are quoted against an explicit floor, e.g. "ledger completes 2 of 5 runs; floor for ranking
   is 3 of 5".

## Item 5 - engine decision for the frozen coding roots

Measured control: the identical model (`qwen3-coder:30b`, Q4) at the identical placement
(`-ngl 999 --n-cpu-moe 48 --load-mode none`) benchmarked on both engines in one protocol:

| Engine | Prefill 1k / 4.9k | Decode 1k / 4.9k |
|---|---|---|
| llama.cpp b10883 (the frozen roots' engine) | 1,230 / 1,319 tok/s | 34.09 / 35.13 tok/s |
| llama.cpp b11461 (today's build) | 1,287 / 1,348 tok/s | 35.44 / 33.95 tok/s |

Differences are within run-to-run noise (~2 %), so **the frozen coding roots stay on b10883**. b11461
is adopted only where a model requires or benefits from its features, and each such root declares it:

- Qwen3.8-27B (probe only): `--fit` placement and the MTP/DFlash speculative heads.
- Nemotron-3.5-Lightning-30B: `nemotron_h_moe` architecture support.
- Kolibri-1: needs the community `hob-b11434` build for the `kolibri1` architecture (no official
  build loads it).
- Strata: its own engine, now v0.1.40.3 in a copied tree.

No frozen root is re-run on a different engine; any future comparison of engines must be declared like
the control above.

## Item 7 - owner decisions to surface

1. **BitLocker status is still unconfirmed.** `manage-bde -status` needs elevation and has never been
   run. The post-install boot succeeded without a recovery prompt after a hardware change, which is
   evidence protection was off or suspended, but that is inference, not a reading.
2. **Whether to close applications to test Q2_0 at a larger resident budget.** At 24 GiB the load
   drove free physical to 0.62 GiB and tripped the 3 GiB floor; at 12 GiB everything holds and it is
   the fastest perfect-scoring configuration. A test at 16 GiB is plausible only if the desktop
   footprint shrinks, i.e. with the owner closing apps. Recommendation: leave it at 12 GiB - the
   12 GiB configuration is already the fastest measured, so a higher budget buys nothing proven.
3. **Whether to adopt the rate-over-n-runs convention (item 2) as lab policy.** It is applied in the
   reports written from today onward.
4. **The 6 GiB worker-private cap question is closed**: 8 GiB was authorized and executed in
   `decisions-20261005-v3`.
5. **Whether to keep pursuing >64 GB models.** Nothing on the shortlist fits: gpt-oss-120b MXFP4 is
   63.4 GB, the original Qwen3.8-Flash-Next at Q4 is over 100 GB. The practical ceiling stays ~78B at
   Q3 or ~35B at Q4.

## Item 8 - hygiene

- `candidates-20261007-v3` (the dense 27B root) stays deliberately unrun; the reason (4.3 tok/s, and
  still 5.0/4.8 tok/s at ctx 8192 in the uniform benchmark, so context is not the blocker) is in its
  README and protocol.
- The 67 GB Q2_0 GGUF staging is **kept**, not deleted: the pack exists and the sha256 record is
  immutable, but the staging is the only local copy of the verified source shards, and 135 GB remains
  free. Delete only if disk pressure appears.
- Two roots were created and then removed within a minute at the start of the rates batch
  (`candidates-20261007-v13-1/-2`): my driver had the wrong gpt-oss filename, the run was killed at
  77 s with no evidence produced, so nothing was lost. The fix and the fault-tolerant driver are in
  `rates-20261007/run_rates.py`.
- All guard trips of today are preserved with their STOP files: `strata-20261007-v7` (Q2_0 at 24 GiB,
  free physical 0.62 GiB) and `strata-20261007-v10` (deep thinking at `reasoning_effort: high` armed
  the sustained-paging guard).
