Repair `merge` so it is correct **and** fast enough for production.

`merge(intervals)` takes a list of `[start, end]` pairs with `start <= end` (closed intervals, integers)
and returns the merged list: overlapping intervals combined, touching intervals combined
(`[1,2]` and `[2,3]` become `[1,3]`), the result sorted by start, and duplicate intervals collapsed.
An empty list returns `[]`. Each input pair must be a list or tuple of exactly two ints (bools are not
ints) with `start <= end`; anything else raises ValueError. The input list must not be modified.

Production requirement: **the function must scale.** The evaluator runs it on 2,000,000 intervals and
requires the result within 15 times the reference implementation's time on the same input, measured in
the same process. A correct quadratic implementation passes every small case and fails this.

Rules: standard library only, do not change the public name or signature, do not modify
`test_public.py` or `README.md`.
