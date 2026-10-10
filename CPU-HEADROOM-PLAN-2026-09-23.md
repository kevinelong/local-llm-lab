# Memory-qualified CPU rerun

Run only after completion-20260923-v1 stops and no other inference is active.
Same pinned Prism runtime, Bonsai PTQ1/PQ2 weights, 8K context, 16 CPU threads,
GPU/KV/operation offload disabled and 600-second request timeout. Reuse the
plain, required-tool and streaming controls and three fixed-prompt repetitions.
These short prompts do not measure long-context performance or agent quality.

Two rounds in reversed order: PTQ1, PQ2, PQ2, PTQ1, each a fresh server and label.
Require 14 GiB physical and 10 GiB commit headroom before each load; require
3 GiB physical and commit headroom while running. A failed threshold invalidates
the case and stops the queue; no partial result is a qualified speed result.
This headroom gate does not prove an absence of paging or other system load.

Memory is sampled approximately every 0.5 seconds, with Windows page-input,
page-read and commit counters approximately every 10 seconds. Counter collection
adds overhead equally across treatments and can take several seconds. Preserve
the raw telemetry; review paging before interpreting a packing difference.
Maximum one hour per case. STOP requests owned-tree termination. No app closure,
pagefile change, new download, or runtime upgrade is authorized by this protocol.

If the resource gate fails before loading, record held and await more memory.
The user was asked to free unused applications or identify specific apps that
may be closed normally; never close the active assistant or unrelated work.
