# Task-manager evaluator v2

Run `python benchmarks/eval_tasks_v2.py <tasks.py-or-directory>`.
The command emits JSON and exits 0 only when every group passes. A nonzero
evaluator exit means inspect its JSON; it is not an infrastructure diagnosis.

The original `examples/eval2.py` remains frozen. Scores from v2 must never be
compared numerically as though they used the same denominator or coverage.

## Contract

The source is copied to a fresh temporary workspace for each of 21 groups.
Every setup command must exit successfully. Expected rejections require exit 1,
a nonempty diagnostic, and no Python traceback. Each command has a five-second
timeout. Commands and output are preserved in the evaluation record.

The checks cover all 16 command/persistence/self-test specification areas:
default fields and timestamps, storage loading, invalid/valid dependencies,
priority validation, list status filters, done blocking, ready filtering and
ordering, dynamic topological priority, cycle exit status, deletion guards and
edge cleanup, ID reuse, block, reverse graph, search, stats, CSV round-trip and
invalid import, self-test preservation, and invalid command/argument handling.

Persisted task state is observed through the specified CSV export interface,
not a mandated private JSON schema. This intentionally couples some groups to
a functioning export command; the detailed command transcript exposes setup
failures. A score is a count of groups, not an independent sample size.

Depth accepts either edges or vertices because the original spec does not
choose a convention. Plan output accepts recognizable task names or ID lines.
Graph output accepts a dependent on the task line or a following indented line.
Unrecognized output is an evaluator limitation to investigate, not automatically
evidence of a reasoning failure. Frozen v2 results include source and evaluator
SHA256 hashes so later scoring changes cannot silently alter their meaning.

The self-test checks verify externally observable isolation and its stated
success message. They do not prove that every requested internal assertion was
executed. The suite is finite: malformed data schemas, very large graphs,
concurrency, and adversarial programs are not exhaustively tested. The temporary
directory and prompt are not a security boundary; run only reviewed lab artifacts.

## Validation

`python benchmarks/validate_tasks_v2.py` rechecks all five archived programs and
uses the archived Astra implementation as a passing control. Fault injection
requires rejection of programs that always crash or always return success, as
well as targeted data-overwrite, swallowed-cycle-exit, no-op import, and ID-reuse
bugs. Both trivial invalid programs must score zero, unlike the historical
scorer's 1/10 crash result. This validates selected failure sensitivity and output
tolerance; it is not a proof that the control implementation is universally correct.

September 20 validation records are under
`C:/Users/kevin/ai_bench/round-20260920/evaluation/`.
