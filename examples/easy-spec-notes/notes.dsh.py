#!/usr/bin/env python3
"""notes.py - a small command-line notes app (Python standard library only).

Notes are persisted to a JSON file ("notes.json" in the current directory).
Every command loads the file at startup and saves after any change; a missing,
empty, or unreadable file is handled gracefully as "no notes".

Commands:
  python notes.py add "some text"   add a note (incrementing integer id + created
                                    timestamp)
  python notes.py list              list all notes: id, done marker, text,
                                    created date
  python notes.py done <id>         mark the note with that id as complete
  python notes.py rm <id>           delete the note with that id
  python notes.py search <term>     list notes whose text contains term
                                    (case-insensitive)
  python notes.py stats             print total notes, number done, number open
  python notes.py test              run self-tests against a temporary data file
"""

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime

DATA_FILE = "notes.json"

USAGE = """usage: python notes.py <command> [args]

commands:
  add "some text"   add a note
  list              list all notes
  done <id>         mark the note with that id as complete
  rm <id>           delete the note with that id
  search <term>     list notes whose text contains term (case-insensitive)
  stats             print total notes, number done, and number open
  test              run the self-tests (uses a temporary data file)
"""


# ------------------------------------------------------------------ storage --

def _empty_store():
    """A brand-new store: ids start at 1 and no notes exist yet."""
    return {"next_id": 1, "notes": []}


def load_store(path):
    """Read the JSON store at path into a Python dict.

    A missing, empty, or otherwise unreadable file never crashes the app -
    it simply produces an empty store. The returned store always has the
    shape {"next_id": int, "notes": [{"id", "done", "text", "created"}, ...]}.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError:
        return _empty_store()

    # Empty file (or whitespace only): start with no notes.
    if not raw.strip():
        return _empty_store()

    try:
        data = json.loads(raw)
    except ValueError:
        return _empty_store()

    if not isinstance(data, dict):
        return _empty_store()

    raw_notes = data.get("notes")
    if not isinstance(raw_notes, list):
        return _empty_store()

    # Keep only well-formed note entries.
    notes = []
    for item in raw_notes:
        if not isinstance(item, dict) or not isinstance(item.get("id"), int):
            continue
        notes.append({
            "id": item["id"],
            "done": bool(item.get("done", False)),
            "text": str(item.get("text", "")),
            "created": str(item.get("created", "")),
        })

    next_id = data.get("next_id", 1)
    if not isinstance(next_id, int):
        next_id = 1
    highest = max((n["id"] for n in notes), default=0)
    if next_id <= highest:
        next_id = highest + 1

    return {"next_id": next_id, "notes": notes}


def save_store(path, store):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(store, fh, indent=2, ensure_ascii=False)


# --------------------------------------------------------------- operations --

def add_note(path, text):
    """Add a note with an incrementing integer id and a created timestamp."""
    store = load_store(path)
    note = {
        "id": store["next_id"],
        "done": False,
        "text": text,
        "created": datetime.now().isoformat(timespec="seconds"),
    }
    store["notes"].append(note)
    store["next_id"] += 1  # ids keep incrementing even after deletions
    save_store(path, store)
    return note


def _find_note(notes, note_id):
    for note in notes:
        if note["id"] == note_id:
            return note
    return None


def mark_done(path, note_id):
    """Mark the note with note_id complete; returns the note or None."""
    store = load_store(path)
    note = _find_note(store["notes"], note_id)
    if note is None:
        return None
    note["done"] = True
    save_store(path, store)
    return note


def remove_note(path, note_id):
    """Delete the note with note_id; returns the removed note or None."""
    store = load_store(path)
    note = _find_note(store["notes"], note_id)
    if note is None:
        return None
    store["notes"] = [n for n in store["notes"] if n["id"] != note_id]
    save_store(path, store)
    return note


def list_notes(path):
    """Return all notes in id order."""
    store = load_store(path)
    return sorted(store["notes"], key=lambda n: n["id"])


def search_notes(path, term):
    """Return notes whose text contains term (case-insensitive), in id order."""
    needle = term.lower()
    return [n for n in list_notes(path) if needle in n["text"].lower()]


def note_stats(path):
    """Return {"total": int, "done": int, "open": int} for the store."""
    notes = list_notes(path)
    done = sum(1 for n in notes if n["done"])
    return {"total": len(notes), "done": done, "open": len(notes) - done}


# --------------------------------------------------------------- formatting --

def format_created(created):
    """Render a stored ISO timestamp as a human-friendly 'YYYY-MM-DD HH:MM'."""
    if not created:
        return ""
    try:
        dt = datetime.fromisoformat(created)
    except (TypeError, ValueError):
        return str(created)
    return dt.strftime("%Y-%m-%d %H:%M")


def format_note(note):
    marker = "x" if note["done"] else " "
    created = format_created(note.get("created", ""))
    return "{} [{}] {} ({})".format(note["id"], marker, note["text"], created)


# ---------------------------------------------------------------------- CLI --

def _parse_id(raw):
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    data_file = os.path.join(os.getcwd(), DATA_FILE)

    if not argv:
        print(USAGE)
        return 1

    command, args = argv[0], argv[1:]

    if command == "add":
        text = " ".join(args).strip()
        if not text:
            print('usage: python notes.py add "some text"')
            return 1
        note = add_note(data_file, text)
        print("added note {}: {}".format(note["id"], note["text"]))

    elif command == "list":
        for note in list_notes(data_file):
            print(format_note(note))

    elif command == "done":
        if len(args) != 1:
            print("usage: python notes.py done <id>")
            return 1
        note_id = _parse_id(args[0])
        if note_id is None:
            print("invalid id: {}".format(args[0]))
            return 1
        note = mark_done(data_file, note_id)
        if note is None:
            print("no note with id {}".format(note_id))
            return 1
        print("marked note {} as done".format(note_id))

    elif command == "rm":
        if len(args) != 1:
            print("usage: python notes.py rm <id>")
            return 1
        note_id = _parse_id(args[0])
        if note_id is None:
            print("invalid id: {}".format(args[0]))
            return 1
        note = remove_note(data_file, note_id)
        if note is None:
            print("no note with id {}".format(note_id))
            return 1
        print("removed note {}".format(note_id))

    elif command == "search":
        term = " ".join(args).strip()
        if not term:
            print("usage: python notes.py search <term>")
            return 1
        for note in search_notes(data_file, term):
            print(format_note(note))

    elif command == "stats":
        stats = note_stats(data_file)
        print("total notes: {}".format(stats["total"]))
        print("done notes: {}".format(stats["done"]))
        print("open notes: {}".format(stats["open"]))

    elif command == "test":
        test()

    else:
        print(USAGE)
        return 1

    return 0


# --------------------------------------------------------------------- tests --

def test():
    """Exercise add, list, done, rm, search, and stats with asserts.

    Everything runs against a file in a temporary directory so real notes in
    the current directory are never touched.
    """
    tmpdir = tempfile.mkdtemp(prefix="notes_test_")
    path = os.path.join(tmpdir, "notes.json")
    try:
        # No file on disk yet: start empty, no crash.
        assert list_notes(path) == []
        assert note_stats(path) == {"total": 0, "done": 0, "open": 0}

        # add: incrementing integer ids plus a created timestamp.
        n1 = add_note(path, "buy milk")
        n2 = add_note(path, "write the spec")
        assert n1["id"] == 1
        assert n2["id"] == 2
        assert n1["done"] is False
        assert n1["created"]
        assert n2["text"] == "write the spec"

        # Persistence: what is on disk matches what was added.
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        assert raw["next_id"] == 3
        assert [n["id"] for n in raw["notes"]] == [1, 2]

        # list: all notes in id order.
        assert [n["id"] for n in list_notes(path)] == [1, 2]

        # done: marks only the requested note complete.
        marked = mark_done(path, 2)
        assert marked is not None and marked["done"] is True
        by_id = {n["id"]: n for n in list_notes(path)}
        assert by_id[2]["done"] is True
        assert by_id[1]["done"] is False

        # rm: deletes only the requested note; unknown ids return None.
        assert remove_note(path, 1) is not None
        assert [n["id"] for n in list_notes(path)] == [2]
        assert remove_note(path, 999) is None
        assert mark_done(path, 999) is None

        # search: case-insensitive substring matching.
        add_note(path, "Buy MILK again")  # id 3
        assert [n["id"] for n in search_notes(path, "milk")] == [3]
        assert [n["id"] for n in search_notes(path, "BUY")] == [3]
        assert [n["id"] for n in search_notes(path, "spec")] == [2]
        assert search_notes(path, "zzz") == []

        # stats counts total / done / open correctly.
        mark_done(path, 3)
        assert note_stats(path) == {"total": 2, "done": 2, "open": 0}

        # Ids keep incrementing even after deletions (never reused).
        n4 = add_note(path, "fourth note")
        assert n4["id"] == 4

        # An empty data file is handled gracefully.
        empty_file = os.path.join(tmpdir, "empty.json")
        with open(empty_file, "w", encoding="utf-8") as fh:
            fh.write("")
        assert list_notes(empty_file) == []
        assert note_stats(empty_file) == {"total": 0, "done": 0, "open": 0}

        # A garbage data file is handled gracefully too.
        bad_file = os.path.join(tmpdir, "garbage.json")
        with open(bad_file, "w", encoding="utf-8") as fh:
            fh.write("this is { not json")
        assert list_notes(bad_file) == []
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("test: all checks passed")


if __name__ == "__main__":
    sys.exit(main())
