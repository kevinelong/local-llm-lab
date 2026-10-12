# Licensing notice

This repository is licensed under the **Functional Source License, Version 1.1, MIT Future License**
(`FSL-1.1-MIT`) - see [LICENSE](LICENSE). In short: you may use, copy, modify and redistribute it for any
purpose except a competing commercial product or service, and each version becomes MIT on its second
anniversary.

Two things that a licence on this repository cannot and does not change:

**1. Third-party data and model outputs inside `instruments/`.** The snapshot includes material derived from
other people's work, and their terms still apply to it:

- `instruments/new-items-20261007/knowledge-items-*.jsonl` is built from published evaluation datasets
  (MMLU and GSM8K), and the fact-list and paper checks are verified against Wikipedia extracts.
- `instruments/bespoke-suite-20261010-v1/` contains per-record outputs over Bespoke's published decision
  suite, and those outputs come from locally served models whose own licences govern them - the lab's notes
  record, for example, that Bespoke-Nimble-9B is **CC-BY-NC-4.0** and local-evaluation-only.
- Everything under `instruments/` was produced locally by measurement; nothing was copied from a vendor's
  repository.

If you want to reuse that material, check the licence of the underlying dataset or model rather than assuming
FSL covers it.

**2. FSL is source-available, not Open Source.** It is not OSI-approved, and it is deliberately not
permissive in one respect: it forbids offering a competing commercial product or service. The 2-year
conversion to MIT is real and irrevocable per version, but until then this repository is not "open
source" in the OSI sense. Do not describe it as such.

## Which terms apply to which version

Versions published before 2026-10-12 were published without an explicit licence file, which under copyright
default means all rights reserved. Adopting FSL-1.1-MIT on 2026-10-12 *grants* rights over those versions
rather than removing any - and nothing here can revoke a grant already made for a version that carried
different terms.

## Vendored third-party material is not in this repository

The lab vendors other people's skill packs outside this repository
(`C:/Users/kevin/.omp/vendor/agent-skills`, `.../anthropic-skills`, `.../superpowers`). None of that code is
copied here, and none of it is relicensed by this file; each keeps its own upstream licence - MIT and
Apache-2.0 for the skills, and source-available terms for the four document skills, which must not be
redistributed.
