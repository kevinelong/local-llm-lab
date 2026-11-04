# iimage review - what the Rust z-image UI is missing against ours

**Subject:** `C:/Users/kevin/iimage` - Win32 + GDI/GDI+ gallery and ComfyUI client,
v0.14.0, 20 commits, 9,551 lines of Rust (`src/view.rs` alone is 6,087).
**Baseline:** `C:/Users/kevin/ai_bench/zimage-web` (FastAPI + browser client, 2,034
lines of Python) and the Tk desktop app it ports.
**Read on:** 2026-11-03. Reading only - nothing built, nothing run, no ComfyUI started.
(A second Rust attempt exists at `ai_bench/zimage-native`, v0.1.0, 2026-10-28: it has the
job/model/transport layers and almost no UI surface, so it is not the comparison.)

## Verdict

iimage is a **strong reader and a thin writer**. The curation half - prompt-family
folders, ranking, sort/filter, gallery, A/B voting - is ahead of ours and is where its
care went. The generation half is one fixed shape: 1024 squared, euler/simple, no
negative prompt, batch 1, no mask, no hires, no size or strength control. Nothing in
the library can be deleted, and no setting survives a restart.

Two consequences worth stating before the list: several sidecar fields it writes are
*not settable* in its own UI (`denoise` is written as `1.0` on a run that used 0.6), and
two Options rows offer values the render then discards. Those are correctness bugs, not
just gaps.

## Missing, ordered by what it costs a user

| missing | ours has | evidence in iimage |
|---|---|---|
| **N-up layouts (1/4/9/16) + sequential batch, one `tile` event per image** | `LAYOUTS`, `sequential`, `batch` | `"batch_size": 1` hardcoded in the graph - `comfy.rs:559` |
| **`ALL` sweep** (every profile once at its ceiling, 1024 px, per-model seeds, profile named in each sidecar) | `ALL_MODEL`, `ALL_SIZE`, `engine.run_all` | `MODELS` is two entries and a render runs exactly one - `view.rs:191`, `view.rs:3097+` |
| **Size picker, 256-1024** | `SIZES` | `let size = 1024i64;` - `view.rs:3108`, although `workflow()` takes width and height |
| **Negative prompt** | `negative` is plumbed through to the UI | graph node exists and is always sent empty: `workflow(..., "", ...)` - `view.rs:3157`, `comfy.rs:542` |
| **Strength / denoise slider** | default 0.70, the measured pose threshold | hardcoded `0.6` - `view.rs:3171`, and no row for it in `option_rows()` (`view.rs:4072`) |
| **Sampler / scheduler choice** | `sampler` parameter | pinned `"euler"` / `"simple"` - `comfy.rs:574-575` |
| **Inpaint with a painted mask** | canvas overlay, `/api/mask`, mask upload | no mask code in the tree |
| **Outpaint / expand** | pad a side | absent |
| **Hires x2 second pass** (denoise 0.45) | `hires` | absent |
| **Cheap preview pass** (2 steps at 256 px, never in the gallery) | `PREVIEW_DIR` | absent; the only preview is the final render |
| **img2img entry point** | any gallery image becomes the base | only through `New...` from an image (`seed_draft_from`, `view.rs:2238`); no base picker, no crop-to-region, no chain (result becomes next base) |
| **Compare base against result, pin a picture for comparison** | both | absent |
| **Stars / starred-only filter** | `favorites` | absent; only vote wins |
| **Delete into a trash with restore and empty** | `.trash/`, `/api/trash*` | **no delete of any kind** - zero `remove_file` in `src/`; listed as "next" in its own README |
| **Multiselect** (cull after voting) | Ctrl+A, shift-click | absent, same "next" line |
| **Prompt history** | Ctrl+Up / Ctrl+Down | no history store |
| **User-saved styles** | `/api/styles` CRUD | five fixed `STYLES`, applied as a comma suffix - `view.rs:190-192, 3099-3103` |
| **Rephrase / enhance / describe through a local LLM** | `/api/rephrase`, `/api/enhance`, `/api/describe`, `synonyms.json` | absent |
| **Settings persistence** (last parameters, favourites, custom styles) | `data/settings.json` | none; every launch starts blank |
| **Workflow-graph viewer and run-log viewer** | `/api/jobs/{id}/graph`, `/api/logs/{kind}` | graph only as a JSON line inside the Ctrl+D block (`view.rs:2614`); log only to `IIMAGE_DEBUG_LOG` |
| **Per-shape VRAM estimate** (turns red within 400 MiB of the card) | `VRAM_POINTS` | free/total VRAM only - `comfy.rs:139-145` |
| **Starter prompts when the library is empty** | yes | empty-library message only |
| **Selecting an image restores prompt + style + seed into the composer** | yes | requires pressing `New...` |

## Defects, not omissions

1. **Steps 12 and 20 are offered and silently discarded.** `adjust_option` cycles
   `[2, 4, 8, 12, 20]` (`view.rs:3533`) and the render clamps to the profile ceiling -
   `clamp(1, profile.max_steps)` = 9 for z-image, 4 for klein (`view.rs:3106`, `3452`).
   The row shows 20 and the graph gets 9.
2. **The sidecar lies about `denoise`.** Every render writes `"denoise": 1.0`
   (`view.rs:3234`) while an img2img run actually used 0.6. Reading the record back
   cannot tell a text-to-image run from a 0.6 re-pose.
3. **Its README is three versions stale.** The `## State` block still ends with
   "real generation behind Render (not started) ... options are stubs ... nothing is
   written to disk", and its header reads 0.7.0, while `Cargo.toml` says 0.14.0 and
   `view.rs:3097+` submits real graphs and writes PNG plus sidecar. The `## Creating
   images` section says the same. Anyone reading the docs to learn the app learns a
   version that does not exist.
4. **Not portable.** `COMFY_PY` and `COMFY_PATHS` are absolute `C:/Users/kevin/...`
   constants (`comfy.rs:25-26`) and the port list is five fixed candidates
   (`comfy.rs:22`). Only `COMFY_HOST` escapes, and there is no equivalent of our
   `ZIMAGE_COMFY_CMD` for a non-ComfyUI-Desktop install.
5. **Checkpoints need a rebuild.** Discovery is dynamic and honest - an unknown UNET is
   reported `unconfigured` - but a profile is a `const` array (`comfy.rs:46-70`), so a
   newly downloaded model cannot be used without recompiling. Ours is one dict entry.

## Where it is genuinely ahead (port these, do not re-derive them)

- **Root-prompt families.** 438 roots fold to 92 folders by word-folding, tail-drift
  merge (12 words and 60 % of the shorter), and label-merge; asserted against the live
  gallery by `cargo test`, so a re-grouping regression fails the build.
- **Folder icons as a 2x2 mini grid** of the group's top four, with 1- and 2-image
  layouts handled.
- **Filter as one precomputed lowercase haystack per image** over every metadata field;
  no field syntax, by Kevin's explicit instruction - "any substring is correct".
- **One sort model driving paint, hit-test and arrow-stepping**, default Wins then
  newest.
- **Full-screen gallery**: zoom to fit / centred / original / 2x / 4x, drag-pan,
  wrapping arrows, slideshow chip, overlays that fade after 2.5 s so nothing reflows.
- **A/B review** with dHash greedy pairing in round one, Swiss rounds after, `vs`
  matrix written into both sidecars, sort back to Wins after each vote.
- **First frame**: desktop colour, then the desktop wallpaper in the OS's own style,
  then content - no white flash (38 ms, logged).
- **Private-desktop smoke run**: 55 assertions, driven by window messages, screenshots
  taken from the app itself, focus never stolen.
- **Baselines**: `baseline.ps1` / `baseline-compare.ps1` record a scenario with the
  machine and version and diff two runs per operation.

## If someone picks this up, cheapest first

1. Wire what the graph already accepts: negative prompt, size, denoise slider,
   sampler. Four rows, no engine work, and it removes defects 1 and 2.
2. Register a save/settings file (last parameters, sort, filter, folder) - the only
   thing that makes a desktop app feel forgotten-day-one.
3. Trash + multiselect + delete, which is already the stated next step and the only
   irreversible gap.
4. Batch/layout + `ALL` sweep - the parity item that changes what the app is for.
5. Masks, hires and outpaint last: they need a canvas layer that does not exist yet.
