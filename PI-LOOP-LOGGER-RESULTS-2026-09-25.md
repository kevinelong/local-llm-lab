# Pi loop logger results - September 25, 2026

Built and tested an opt-in observation-only Pi 0.86.1 extension.
[Full report](../ai_bench/pi-loop-logger-20260925-v1/REPORT.md).
[Usage and limits](../ai_bench/pi-loop-logger-20260925-v1/README.md).

- Nine behavior checks passed; native Pi controls preserved 18 calls/results
  across enabled, disabled, and unwritable-log modes. No judge-model calls.
- Three fresh serial OmniCoder sessions produced 95 tool calls. One reviewer
  labeled raw histories before opening observer logs: 40 stalled calls in one
  prolonged episode, seven uncertain calls excluded, 48 negative calls.
- Exact-match logger missed the entire loop because each command appended one
  more credit/debit transaction. It falsely flagged one legitimate fallback
  from a malformed inline test command to the canonical public-test file.
- Live categories exactly match offline replay for all three sessions.
  Instrumented hooks averaged 0.050 ms, max 0.321 ms across 193 handlers;
  ready/end writes are excluded, and this is not a controlled slowdown study.
- Ledger timed out at 180s and failed correctness; events finished cleanly
  and passed; paths finished cleanly but failed external correctness. Loop
  labels do not certify code quality.
- The first queue stopped before a second inference on a transient
  llama-server process. Ownership was not established; subsequent inspection
  found no model processes/listeners. Original evidence is preserved. A v2
  continuation added only a bounded settle wait and ran the two unstarted
  sessions with byte-identical logger code.
- Memory gates held. All 100 sampled owned process identities absent; owned
  Windows Jobs empty; temporary server port and locks cleared. No reboot,
  startup changes, global installation, or automatic intervention.

Do not enable automatic interruption. Next candidate is operation/test-target
similarity plus progress tracking, keeping this exact-match implementation as
a baseline. Develop it separately and validate on new histories. One reviewer
and three correlated task histories do not establish general performance.
