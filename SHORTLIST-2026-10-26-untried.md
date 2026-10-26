# Untried work, 2026-10-12 → 2026-10-26

The two-week window produced **12 daily scans** (10-14 to 10-26; 10-15 and 10-13 are missing from the run log) and **9 executed items**. This file is the remainder, ranked by
leverage per unit of cost, and it deliberately goes outside the feeds we have been reading where the gap is wider than
anything on the shortlists.

## What actually ran (so it is not proposed again)

| item | result |
|---|---|
| decision track on Ollama's native path | closed, 14/18, 0/4 caught, 94 ms median (`ollama-decision-20261020/`) |
| `--moe-cache-mib` ladder + ceiling | done: 47.4 → 78.3 tok/s, admissible ceiling **5,376 MiB** (q2, q2c) |
| Strata KV residency | done: **7.6 → 69.1 tok/s**, repeat 83.0 (q1) |
| engine 0.1.40.3 vs 0.1.47 | done: text- and speed-neutral on our pack (q7) |
| 0.1.47 staged, first load, #3699 reachability | done (`STRATA-0.1.47-FIRST-LOAD-2026-10-22.md`) |
| WDDM shared segment | done: **17.8 GiB** of a ~31.7 GiB cap under one resident arm |
| tensor types of our staged pack | done: all 40 routed-expert downs at Q4_K |
| mlock/TTFT on b11823 | done: a **no-op for our model**, no buffer over 4 GiB (`TTFT-MLOCK-AB-2026-10-22.md`) |
| resource audit / orphan check, Django + OS patches | done (2026-10-22) |

## A. Carried by our own shortlists and still unrun

Ranked by what it would change. Costs are for this box.

1. **Prompt-chunk ladder on 12 GB: 4096 (default) vs 8192 vs 16384.** Every scan since 10-25 carries this, and today's
   headline makes it the biggest single lever in the list: on a **24 GB** 5090 D, `--prefill-chunk 16384` is **4.2×** the
   auto 8192 (prefill 217.7 → **907.9** tok/s at 7.3k, long-prompt TTFT ~34 s → **~8 s**, same answers), and 32768
   regresses. The vendor rule puts **our** class at 4096, and **nobody has published a 4096-vs-8192-vs-16384 row on 12
   GB**. Cost: engine starts only, no download. Gate: none.
2. **`--moe-cache-cpu-share` at rung 0 and rung 5,376, share 0 / 0.5 / 0.95, under `--cpu-moe`.** The PR's own table says
   the sign flips with capacity (24.2 → **47.6** tok/s at 6464 MiB, 65.5 → **54.1** at 19392). Our whole ladder was taken
   at share 0, so the knob is unmeasured here. Needs a build from the PR.
3. **`--vram-reserve-mib` 900 vs the shipped 1536 at a fixed cache.** #3952 says the reserve stopped being scratch space
   and became *budget* between 0.1.43.1 and 0.1.46; a quiet bump at 1536 may be masking that. Two starts per reserve.
4. **Cold-vs-cold expert-profile pair, n ≥ 2 starts per arm.** Carried since **10-16**; #1332 quotes an 8-28 % spread.
   This is the only item that has survived four shortlists unchanged, and it is cheap (four starts).
5. **Cliff test + declared-versus-granted readback.** A requested cache size that the engine silently clamps is the
   failure our q2c row found by accident; nobody has asserted the two numbers against each other deliberately.
6. **Idle-VRAM accounting across desktop states, then the display move if it pays.** New today. Our "idle" figure has
   read 1.3, 1.7 and 9.6 GiB on this box in one day, and we do not know which of those is the desktop.
7. **KV geometry: `--kv k8v4` vs `--kv int8`, then a context ladder at 4K/16K/32K.** Arrived 10-25 from Reddit, carried
   ever since. One arm each plus three rungs.
8. **Strata bump to 0.2.6 / engine 0.1.50 as a defaults experiment.** The declaration list is now **eight** items
   (pagefile/commit, reserve 1536, MTP off, free VRAM per request, overlap read back, chunk size read back, five workers,
   conversation cache auto). Two independent confirmations arrived this week, including #3966 resolved. **Gated on you** -
   120 pinned digests.
9. **`Qwen3-Coder-30B-A3B-Instruct` Q4_K_M, 16.75 GiB, on the 414-check metric.** Carried on six consecutive shortlists.
   One download, and it is the only first-party 30B-class coder in our shape.
10. **Flint 21.78 GiB / Kolibri Q3_K_M on a stock build ≥ b11719.** Three weeks unrun; each is one download and one build.
11. **`H2O-Lightning-4B` then `pplx-decider:27b` on `/v1/systemone`.** The decision track's remaining arm, after the
    native path closed.
12. **`STRATA_ADAPT_OVERLAP` on 0.1.46+, interleaved rounds.** The guard misreads `--layer-split`; whether it also
    misfires on a single card is unverified and decides if the overlap lever is reachable here.
13. **Our learned `.strp` hot set vs the cache behaviour the log reports.** We hold a 196,632-byte profile learned on
    2026-10-16 and have never checked it against a run.
14. **Windows file-cache switch (#3059) and a native Colibri build.** Both need a build, both parked for that reason.

## B. Not on any shortlist, because our feeds do not cover these

The first three are free or nearly free *today*, with weights already on disk.

15. **ComfyUI `int8_convrot` vs `nvfp4` for z-image.** Both files are **already local** - `z_image_turbo_int8_convrot`
    (6.20 GiB) and `z_image_turbo_nvfp4` (4.51 GiB) - and the server's own log advertises convrot kernels
    (`quantize_convrot_w4a4_weight`, `dequantize_int8_convrot_weight`). We have only ever run nvfp4. This is a free
    quantisation A/B on the model we use most.
16. **The knobs we have fixed without measuring on the flux2 profiles:** cfg (assumed **1.0** for every profile, while
    `flux1 dev` used 3.5 and the pose work showed guidance matters), the negative prompt (we always pass **empty** - is it
    even read on a distilled model?), and sampler/scheduler (only `euler`/`simple` ever ran; `uni_pc`, `dpmpp_2m`,
    `res_multistep` and `karras` are installed). A 3×3×2 grid at 512 px is an afternoon and would remove three
    assumptions from every image row we have published.
17. **The 9B's own strength/pose ladder.** The denoise threshold (0.70) was measured on **4B klein, dev and z-image**.
    The 9B is now the best-scoring editing candidate and has never been swept. 4 strengths × 2 seeds ≈ 8 images.
18. **A local VLM judge.** Nothing vision-capable is installed, which is the only reason the anatomy probe and any
    on-box image rubric are still unmeasured; it also keeps nude/figure studies off the cloud. One ~5 GiB pull
    (`minicpm-v`, a Qwen-VL build) makes the image track self-contained.
19. **Train a small LoRA on our own diagram corpus.** The one failure no prompt revision fixed is **label binding** -
    tree leaves carry the prompt's own numbers instead of 1..7 (1/7 at every density, 12/14 for z-image at 1024). That is
    a content problem, and a 200-image LoRA on our frozen corpus is the untried lever. 12 GB, kohya or diffusion-pipe,
    a few hours.
20. **Pose conditioning for the editing gap.** `pose_probe.py` concluded the right tool is an instruction-edit checkpoint
    or ControlNet/OpenPose, and neither is installed. This is the standard fix for "move the figure, keep the face".
21. **Wan 2.2 steps and frames.** We measured 49 frames @30 steps and 121 @30. Steps 20/40 and 81 frames at 704² are
    uncharted, and steps are the only throughput knob that does not change the grid.

## What I would do next, in order

1. **#15 and #16** - free, local, and they correct assumptions baked into every image row we have published.
2. **#1** - the chunk ladder; the largest unmeasured lever in the lab, on the engine we are about to bump to.
3. **#18** - one download that unblocks the whole image-measurement side.
4. **#4 and #5** - the two cheapest corrections to numbers we already quote.
5. **#9** - the one model carried on six shortlists that has never been downloaded.
