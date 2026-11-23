"""How big is the evidence we would commit? Report it, and say when it crosses the agreed budget.

Kevin's rule (2026-11-23): research evidence under 10 MB is included with a discussion or report **without asking**;
above that, ask first. Raw model replies are kept because a scorer fix can then be audited and re-applied without
running inference again - that has already caught four defects in one day - so this is a budget, not a ban.

  python tools/evidence-size.py [--budget-mb 10]
"""

import argparse
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
EVIDENCE = ["results", "data"]


def size_of(paths):
    total, count = 0, 0
    for name in paths:
        directory = ROOT / name
        if not directory.exists():
            continue
        for file in directory.rglob("*"):
            if file.is_file():
                total += file.stat().st_size
                count += 1
    return total, count


def tracked_size():
    """What git would actually carry: the same paths, limited to files git knows or would add."""
    try:
        listing = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "-z"],
                                 cwd=ROOT, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    total, count = 0, 0
    for raw in listing.split(b"\0"):
        if not raw:
            continue
        relative = raw.decode("utf-8", "replace")
        if not any(relative.startswith(name + "/") for name in EVIDENCE):
            continue
        file = ROOT / relative
        if file.is_file():
            total += file.stat().st_size
            count += 1
    return total, count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget-mb", type=float, default=10.0)
    args = parser.parse_args()

    on_disk = size_of(EVIDENCE)
    tracked = tracked_size()
    budget = args.budget_mb * 1024 * 1024
    print("evidence on disk: %.2f MB in %d files (%s)" % (on_disk[0] / 1048576, on_disk[1], ", ".join(EVIDENCE)))
    if tracked:
        print("committable:      %.2f MB in %d files" % (tracked[0] / 1048576, tracked[1]))
        subject = tracked[0]
    else:
        subject = on_disk[0]
    remaining = budget - subject
    if remaining >= 0:
        print("budget %.0f MB: %.2f MB left - include without asking" % (args.budget_mb, remaining / 1048576))
    else:
        print("budget %.0f MB: OVER by %.2f MB - ask before committing more evidence"
              % (args.budget_mb, -remaining / 1048576))


if __name__ == "__main__":
    main()
