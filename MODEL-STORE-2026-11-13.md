# Model store, 2026-11-13: uncensored + fits + coding, and the swap it produced

Rule (Kevin, today): a candidate must be **uncensored**, must **fit** this box (12,227 MiB VRAM, 63.5 GiB RAM),
and the work must be **coding**. Two corrections came with it the same day and are part of the rule:

- **Speed is a declared field, never a veto.** A slow model stays a candidate when its reasoning or knowledge
  measures higher than the retained set, because those tasks do not care about tok/s.
- Therefore **"fits" means memory only**; a dense model is admissible to about 20 GB.

## What the store did

| | models | blobs | C: free |
|---|---|---|---|
| before | 27 (19 aliased) | 156.5 GB | 80.2 GB |
| after the supersession pass | 11 | 100.8 GB | 135.9 GB |
| after this swap | **8** | **73.5 GB** | **127.3 GB** |

Removed, each superseded by something already on disk or by the rule itself: `granite3-moe:3b` (4096-token context,
unusable for our ~9.5 k prompt) -> `granite4.2:8b`; `qwen3:30b-a3b` -> the Qwen3.6-35B-A3B pack; `ornith-1.5:9b`
-> `qwen3.5:9b` (its manifest is the newer, 2026-09-09 against 2026-08-20); and `qwen3-coder:30b` -> the abliteration below.

## The coder swap, measured

`ggml-org` publishes **no newer coder** than `Qwen3-Coder-30B-A3B` (its newest repos are Qwen3.8-Flash-Next,
Qwen3.8-27B, Qwen3.6-35B-A3B, Qwen3.6-27B), so the replacement had to be a variant, not a release:

`hf.co/mradermacher/Huihui-Qwen3-Coder-30B-A3B-Instruct-abliterated-i1-GGUF:IQ4_XS` - 16 GB, 134,611 downloads,
the same 30B-A3B shape as the model it replaces.

| field | value |
|---|---|
| load | **19.4 s**, 19 GB resident |
| split | **47 % CPU / 53 % GPU** (`ollama ps`) |
| context | **32,768** |
| decode | **28.1 tok/s** (47 tokens, temp 0) |
| first task | a `uniq_preserve` one-liner, **correct on the first try** |
| gates at load | 29.84 GiB physical, 16.53 GiB commit, 8,833 MiB VRAM free - all floors clear |

The censored `qwen3-coder:30b` (18 GB, 34 tok/s) is gone; **28.1 against 34 tok/s is the price of the 47 % CPU
share**, and it is recorded rather than argued.

## Rejected - and the two that fit

Memory rejections only, with the number that rejects them: `Huihui-Qwen3-Coder-Next-abliterated` **IQ4_XS 43.1 GB**;
`Qwopus3.6-35B-A3B-Coder-Uncensored-Genesis-MTP` ships **Q8_0 37.8 GB** only; `Abiray/DeepSeek-V4.1-Flash-Uncensored`
231 GB+.

**Admissible on the memory rule and now downloading:** `DavidAU/Qwen3.8-27B-TURBO-Fable-...-Heretic-Uncensored-NEO-CODER-MAX-MTP`,
**1.6 M downloads**, uncensored, coding, **MTP head**, dense 27B - quants `MTP-IQ4_XS 17.0 GB`, `MTP-Q4_K_S 17.5`,
`MTP-Q4_K_M 18.5`, `LOW-MTP-IQ4_XS 15.3`. Its unaccelerated dense rate here is **4.3 tok/s**, which is a
*quality-at-leisure* cost, not a disqualification: it is admitted for offline batch, planning and hard one-shots.

**The test that decides it**: the 414-check ranked subset and the 1,100-item knowledge instrument, against
Qwen3.6-35B-A3B (**414/414**, 88.5-89.7 %). If it does not measure higher, it stays a convenience rather than a
retained model - which is the same standard every other row here has met.
