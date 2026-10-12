Repair one function in a large legacy module.

`legacy.py` is a production module of ~1800 small helpers. Exactly one function is wrong:
`reconcile_batch(records)`.

Specification of `reconcile_batch(records)`:
- `records` is a list of `(account, cents)` pairs, processed in order.
- `account` must be a nonempty string equal to its own `strip()`; anything else raises ValueError.
- `cents` must be an int (bool is not an int) and must be >= 0; anything else raises ValueError.
- Return a list of `(account, total, count)` tuples sorted by account, where `total` is the sum of that
  account's cents and `count` is how many records that account had. Every record counts, including
  zero-cent records. An empty list returns `[]`.

Rules:
- Fix `reconcile_batch` only. **Every other function in `legacy.py` must keep its exact source.**
- Do not add or remove functions, do not modify `README.md` or `test_public.py`, and use only the
  Python standard library.
- Run the public tests, then audit the cases they do not cover. Finish with a brief summary.
