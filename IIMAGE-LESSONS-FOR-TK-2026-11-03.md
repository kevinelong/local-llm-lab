# What to steal from iimage for our Tk/Python build

> **Corrected 2026-11-03, after the map was taken.** This note was written from the Rust app alone. A structural map of
> `ai_bench/image-models-20261020/zimage_ui.py` (12,749 lines) then showed that **most of these mechanisms already exist
> there**, several with the measurement that motivated them: `_photo_of` keyed by `(path, bucket)` in a bounded LRU
> ("9.5 ms a tile, 172 ms for 18" before it), `.thumbs` on disk, one 60 ms poll with a single coalesced thumbnail repaint,
> `_prefetch(ahead=2)`, `LoadingMeter` with measured percentages and the <1 s / 1-3 s / >3 s rule, 1/2/3/4-picture folder
> sheets, and an always-on `_Profile` with p50/p90. Read this as a **checklist of what a gallery like this should have**,
> not as a list of gaps. The three that were genuinely missing are fixed in that repo at v0.28.0 and written up in its
> `STATE-2026-11-03.md`; the two that remain (per-refresh widget destroy/recreate, and a photo-cache miss decoding on the
> UI thread) are named there as design work.

**Source read:** `C:/Users/kevin/iimage` (Rust, Win32 + GDI/GDI+, v0.14.0), 2026-11-03.
**Target:** our own reimplementation of the z-image UI in Tk + Pillow.
**Scope:** mechanisms, not features - the feature gap is in
`IIMAGE-REVIEW-2026-11-03.md`. Nothing was built or run; every claim is from its source,
with the file and line it came from.

---

## 1. One retained view model, and every consumer reads it

`rebuild_visible()` (`view.rs:1222-1310`) computes the sorted, filtered list **once**
per change - sort, filter, screen, reload - and stores it in `self.visible`. Painting,
hit-testing, keyboard stepping and the scrollbar all index that same list
(`step_image` at `view.rs:1190-1215` steps through `self.visible`, explicitly "the
sorted, filtered list"). Its own instrumentation says the rebuild is free: **0.013 ms
mean, 0.035 ms p95** for 326 items.

Why it matters: the classic Tk gallery bug is sorting inside a draw callback, so paint
order, click order and arrow order can disagree. Two orders cannot disagree if there is
one list.

**In Tk:** `self.visible: list[Entry]`, each with `(index, rect)`; `relayout()` on
`<Configure>`, sort change, filter change; `canvas` handlers and key bindings look up
`self.visible`, never re-derive it.

## 2. Decode once, at final size, then blit

`imaging.rs:1-3` states the rule the app is built on: *"Each image is rendered once into
a letterboxed DIB section at exactly the size it will be shown at, so painting stays pure
GDI blits and never pays for scaling twice."* Decode is GDI+ first with a WIC fallback
for WebP (`imaging.rs:97-104`), so the format list is the OS's, not a python plugin's.

Two caches with **different keys**, because the same file is drawn at two sizes:
tiles by image index (`view.rs:4735`), folder icons by `(image, w, h)` (`view.rs:4704`),
each with an explicit bounded FIFO eviction that also frees the bitmap
(`TILE_CACHE_CAP = 240`, `ICON_CACHE_CAP = 300`, `view.rs:32-34, 4713, 4749`).

**In Tk/Pillow:**
- `Image.open(p)` → `.draft('RGB', (w, h))` for JPEG (decode straight to ~target size),
  then one `thumbnail((w, h), LANCZOS)` → `ImageTk.PhotoImage`.
- Cache key `(path, w, h, mtime)`, cap the dict, evict oldest. **The opposite hazard from
  theirs:** Tk drops a PhotoImage that nothing references, so the cache must *hold* the
  reference - that is the "thumbnails go blank after scrolling" bug.
- Never `Image.resize` inside a redraw. At 240 tiles a full-viewport repaint that
  rescales is hundreds of ms; a blit of already-sized bitmaps is one screen copy.

## 3. One heartbeat timer, one repaint per tick

A single 80 ms `SetTimer` (`main.rs:161`) drives everything that polls: loading progress,
thumbnail prefetch, render progress, caret blink, overlay fade, slideshow, the ComfyUI
probe (`main.rs:492-510`). Each tick ORs a `repaint` flag and invalidates **once** at the
end - not one invalidate per subsystem.

**In Tk:** one `root.after(80, tick)` doing the same, ending in a single
`update_idletasks()`; batch canvas changes with `itemconfigure`/`coords` calls and let one
`after_idle` do the repaint. Never `after(0)` chains per widget, and never `update()`
inside a callback.

## 4. Prefetch just outside the viewport, on a budget

`prefetch_tick(2)` (`view.rs:1087-1150`) decodes **two** items per tick, only in rows
`[first_row - 1, last_row + 2]`, and returns immediately if a menu is open or the screen
is not a grid. Scrolling one row therefore lands on decoded thumbnails.

**In Tk:** same geometry (`rows = viewport // (card_h + gap)`), budget 2-4 per tick,
`if self.menu_open or screen not in (GRID, FOLDER): return`. This is the whole fix for
"scroll feels sticky" without a second thread.

## 5. Loading is a screen with phases, not a freeze

`Library::load_with(dir, on_progress)` reports `LoadProgress{phase, done, total}`
(`data.rs:207-260`) over an `mpsc` channel from a worker thread; the loading screen shows
"scanning the folder...", "reading metadata 420 of 1200 images", "3 of 18 thumbnails",
each with a determinate bar (`view.rs:2281-2330`, `4838`). Sidecars are parsed in
parallel chunks with the thread count **capped at 8** (`data.rs:627-632`,
`available_parallelism().clamp(1, 8)`), and after the load a `begin_warmup` queue decodes
exactly the first page so the first real paint is not a stall.

**In Tk:**
- `queue.Queue` + poll in the heartbeat; never `join()` on the UI thread.
- `ThreadPoolExecutor(max_workers=min(8, os.cpu_count()))` for sidecar parsing - the cap
  is deliberate and matches our own "-t 16 beats -t 24" finding: past the memory
  bandwidth knee more threads only add contention.
- Progress callback signature `(phase: str, done: int, total: int)` so every long step
  can reuse the same screen.

## 6. No white flash on the first frame

Window background is `COLOR_DESKTOP`; on erase it fills that colour, blits the desktop
wallpaper in the OS's own style (center/tile/stretch/fit/fill/span, decoded from
`Control Panel\Desktop`), and only then paints content (`view.rs:669+`, 38 ms, logged as
`desktop.wallpaper`).

**In Tk:** `root.configure(bg=<desktop colour>)` **before** `deiconify()`, then a
placeholder frame drawn from the same layout function; Tk's default light-grey flash is
the same defect.

## 7. Paint into a buffer, and give the app a way to photograph itself

Everything paints to `mem_dc`, then one `BitBlt` to the window (`view.rs:4928-4990`).
`WM_PRINT`/`WM_PRINTCLIENT` are implemented, and `WM_APP+1` with `IIMAGE_FRAME_DIR` set
writes the **current screen** to a BMP (`main.rs:50, 511-522`) - which replaced
`PrintWindow`, whose DWM surface was stale often enough on a private desktop to make
pixel checks flake.

**In Tk:** `canvas.postscript` is not the answer. Instead keep draw code as
`render(target, layout)` where `target` is either the canvas or a `PIL.ImageDraw`; a
`--screenshot <path>` mode then renders the *same* layout headless, and tests assert on
pixels without a display or a window manager.

## 8. Diagnostics as one paste-ready block

`Ctrl+D` (`view.rs:2537-2620`) emits, in one block: version + pid, window size, screen,
sort and filter, ComfyUI host/up/vram, loader availability with `checked_ms`, UNETs
discovered but unconfigured, profile usability and missing filenames, the draft's
parameters, the render phase + error + elapsed, and the exact API graph sent.

That block is the whole support surface for a bug report, and it costs one function.

**In Tk:** same, plus `sys.version`, PIL version, resolved settings path, and the last
exception traceback.

## 9. Say "cannot ask", never "missing"

`Available = HashMap<&'static str, HashSet<String>>` where `None` means the probe failed
(`comfy.rs:76-80`). The render guard is `available.is_some() && !missing.is_empty()`
(`view.rs:3090-3096`) - so an unreachable server never greys every model, and a model
the server offers without a known wiring is shown as `unconfigured` rather than offered
and broken. A server is only stopped if **this process started it** (`comfy.rs:506-520`).

**In Tk:** the same tri-state (`unknown | ok | missing`) in the model list, and the same
ownership flag around any subprocess we launch.

## 10. Filter on a precomputed haystack

`haystack_of(file, ext, meta)` builds one lowercase blob per image at load
(`data.rs:119-160, 271`); a keystroke is one `str.contains`. Folder matching is
`label.contains OR any member's haystack` (`view.rs:1200-1218`). No field syntax, by
design.

**In Tk:** build it at load, patch it when a sidecar is rewritten; do not walk twenty
fields per keystroke.

## 11. Tolerate the folder you did not write

Both the groups file and every sidecar are read with a UTF-8 BOM stripped, because
`PowerShell Set-Content -Encoding utf8` adds one and JSON does not allow it
(`data.rs:223-228, 640-650`). Malformed JSON means "no metadata for that image", never a
failed load; a missing groups file falls back to disk enumeration plus an
`unfiled (n)` folder (`data.rs:440-452`).

**In Tk:** the same two rules. Our sidecars come from three different producers, so this
is not hypothetical.

## 12. Hit-test honesty and per-screen scroll memory

- A right-click menu acts on **the item that opened it**, not the item under the menu -
  fixed in 0.5.0 and pinned by a test that opens tile 0's menu and clicks over tile 1.
- Back from a folder returns to the folder grid **at the scroll position you left**, per
  screen (`view.rs:1155`, `reload`).
- Arrow keys step the sorted, filtered list; `PgUp`/`PgDn` step folders in the grid's
  order, not the folder's.

## 13. Profiling that pays for itself the first afternoon

`prof::perf(op, started)` wraps anything over 1 ms; counters record non-durations
(`paint.cards`, `prefetch.tiles`, `decode.failures`); at exit a summary prints
count/total/mean/p50/p95/max per operation. `baseline.ps1` records a scenario with the
machine and version, `baseline-compare.ps1` prints per-operation deltas.

Its first baseline immediately showed `msg.paint` p95 23 ms with a **407 ms first
paint** - i.e. the number that makes "the UI feels slow" falsifiable.

**In Tk:** `perf_counter()` around the same operations, `atexit` summary, and a
`run.log` you can diff. Cheap, and it is the difference between tuning and guessing.

## 14. Golden assertions against the real corpus

`cargo test` asserts, on the live gallery, that no root is split, similar roots share a
folder and no two folders share a label; `Library::load` logs
`folder '<label>' images=N top=<file>` (`data.rs:452-475`) so a harness checks grouping
and ordering **without reading pixels**.

**In Tk:** a `--dump-grouping` mode and tests over its output. That is what keeps a
grouping rule true as the gallery grows from 92 to 200 folders.

## 15. Test through the app, not the desktop

`scripts/isolated.ps1` creates a **private desktop**, starts the app there, drives it
with window messages, and asserts 55 things (grouping counts, icon choice, paging, scroll
restore, menu targeting, stepping, `F5` reload, New/Generate/Render/Back, sort and filter,
Open-folder dialog cancel, gallery zoom/slideshow, probe-without-autostart, a vote landing
in a sidecar, theme resolution). Nothing appears on the real desktop and focus is never
taken.

**In Tk:** construct widgets, call the handlers directly without `mainloop`, and render
to Pillow for pixel assertions. Same idea: the test drives the app's own code paths, and
never depends on a human's screen.

---

## Do not copy these

- **Fixed 1024 px, hardcoded 0.6 denoise, empty negative prompt, euler-only** - the gap
  list, and each one is a parameter the graph already accepts.
- **Absolute `C:/Users/kevin/...` paths in source** (`comfy.rs:25-26`). Read them from
  env or a config file; a second machine is not an exotic case.
- **A steps list the render clamps away** (`view.rs:3533` vs `3106`). If an option is
  offered it must reach the graph, or the option list must be generated from the
  profile's ceiling.
- **A state block that drifts three versions.** Keep the version in one constant and
  generate the state line from it, then assert it in a test - we already have the
  single-constant rule; this is the same rule applied to prose.

## Transfer table

| iimage mechanism | Tk/Pillow form | what it buys |
|---|---|---|
| retained `visible` list | `Entry(index, rect)` rebuilt on change | paint, click and arrow order cannot disagree |
| pre-sized letterboxed bitmaps | `thumbnail()` once, cached `PhotoImage` | no rescale per repaint; the big one |
| bounded tile/icon caches | dict + FIFO eviction (keep refs) | flat memory on a 3,000-image folder |
| 80 ms heartbeat | one `after(80)` tick, one repaint | steady input latency under load |
| prefetch 1 row out, budget 2 | same geometry in the tick | scrolling lands on decoded thumbnails |
| worker + `LoadProgress` | `ThreadPoolExecutor(<=8)` + `queue.Queue` | determinate loading, no frozen window |
| desktop colour then wallpaper | `bg=` before `deiconify` + placeholder | no grey flash |
| `WM_APP+1` frame dump | `--screenshot` via `PIL.ImageDraw` | headless pixel tests |
| `prof::perf` + baselines | `perf_counter` + `atexit` summary | performance work you can prove |
| precomputed haystack | lowercase blob per image | instant filtering with no schema |
| tri-state availability | `unknown/ok/missing` | no false "model missing" |
