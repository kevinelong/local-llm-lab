#!/usr/bin/env python3
"""notes - a small command-line notes app (standard library only)."""

import json
import os
import sys
import tempfile
from datetime import datetime

DATA_FILE = "notes.json"


def load_notes(path=DATA_FILE):
    """Load notes from the data file, tolerating a missing or empty/corrupt file."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return []
        data = json.loads(content)
        if not isinstance(data, list):
            return []
        return data
    except (json.JSONDecodeError, OSError):
        return []


def save_notes(notes, path=DATA_FILE):
    """Persist notes to the data file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2)


def next_id(notes):
    """Return the next incrementing integer id."""
    if not notes:
        return 1
    return max(note["id"] for note in notes) + 1


def add(text, path=DATA_FILE):
    """Add a note with an incrementing id and a created timestamp."""
    notes = load_notes(path)
    note = {
        "id": next_id(notes),
        "text": text,
        "done": False,
        "created": datetime.now().isoformat(timespec="seconds"),
    }
    notes.append(note)
    save_notes(notes, path)
    print(f"Added note {note['id']}.")
    return note


def _created_date(note):
    """Return just the date portion of a note's created timestamp."""
    created = note.get("created", "")
    return created.split("T")[0] if "T" in created else created


def list_notes(notes=None, path=DATA_FILE):
    """List all notes showing id, done marker, text, and created date."""
    if notes is None:
        notes = load_notes(path)
    if not notes:
        print("No notes.")
        return
    for note in notes:
        marker = "[x]" if note.get("done") else "[ ]"
        print(f"{note['id']:>3} {marker} {note['text']} ({_created_date(note)})")


def done(note_id, path=DATA_FILE):
    """Mark the note with the given id as complete."""
    notes = load_notes(path)
    for note in notes:
        if note["id"] == note_id:
            note["done"] = True
            save_notes(notes, path)
            print(f"Marked note {note_id} as done.")
            return True
    print(f"No note with id {note_id}.")
    return False


def rm(note_id, path=DATA_FILE):
    """Delete the note with the given id."""
    notes = load_notes(path)
    remaining = [note for note in notes if note["id"] != note_id]
    if len(remaining) == len(notes):
        print(f"No note with id {note_id}.")
        return False
    save_notes(remaining, path)
    print(f"Removed note {note_id}.")
    return True


def search(term, path=DATA_FILE):
    """List notes whose text contains term (case-insensitive)."""
    notes = load_notes(path)
    term_lower = term.lower()
    matches = [note for note in notes if term_lower in note["text"].lower()]
    list_notes(matches)
    return matches


def stats(path=DATA_FILE):
    """Print total notes, number done, and number open."""
    notes = load_notes(path)
    total = len(notes)
    done_count = sum(1 for note in notes if note.get("done"))
    open_count = total - done_count
    print(f"Total: {total}")
    print(f"Done:  {done_count}")
    print(f"Open:  {open_count}")
    return total, done_count, open_count


USAGE = """usage: python notes.py <command> [args]

commands:
  add "text"     add a note
  list           list all notes
  done <id>      mark a note as complete
  rm <id>        delete a note
  search <term>  find notes containing term (case-insensitive)
  stats          show note counts
  test           run the self-test"""


def usage():
    print(USAGE)


def _parse_id(value):
    """Parse an id argument, returning an int or None if invalid."""
    try:
        return int(value)
    except ValueError:
        return None


def main(argv):
    if len(argv) < 1:
        usage()
        return 1

    command = argv[0]
    args = argv[1:]

    if command == "add":
        if not args:
            usage()
            return 1
        add(args[0])
    elif command == "list":
        list_notes()
    elif command == "done":
        if not args or _parse_id(args[0]) is None:
            usage()
            return 1
        done(_parse_id(args[0]))
    elif command == "rm":
        if not args or _parse_id(args[0]) is None:
            usage()
            return 1
        rm(_parse_id(args[0]))
    elif command == "search":
        if not args:
            usage()
            return 1
        search(args[0])
    elif command == "stats":
        stats()
    elif command == "test":
        test()
    else:
        usage()
        return 1
    return 0


def test():
    """Exercise add, list, done, rm, search, and stats against a temp data file."""
    fd, tmp = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    os.remove(tmp)  # ensure "missing file" path is exercised
    try:
        # Missing file loads gracefully.
        assert load_notes(tmp) == []

        # Empty file loads gracefully.
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("")
        assert load_notes(tmp) == []

        # add
        n1 = add("Buy milk", tmp)
        n2 = add("Walk the dog", tmp)
        n3 = add("Read a MILK carton", tmp)
        assert (n1["id"], n2["id"], n3["id"]) == (1, 2, 3)
        assert all("created" in n for n in (n1, n2, n3))
        assert not n1["done"]

        notes = load_notes(tmp)
        assert len(notes) == 3

        # list (just verify it runs without error)
        list_notes(path=tmp)

        # done
        assert done(2, tmp) is True
        assert done(99, tmp) is False
        assert load_notes(tmp)[1]["done"] is True

        # search (case-insensitive)
        matches = search("milk", tmp)
        assert {m["id"] for m in matches} == {1, 3}
        assert search("nothing here", tmp) == []

        # stats
        total, done_count, open_count = stats(tmp)
        assert (total, done_count, open_count) == (3, 1, 2)

        # rm
        assert rm(1, tmp) is True
        assert rm(1, tmp) is False
        remaining = load_notes(tmp)
        assert {n["id"] for n in remaining} == {2, 3}

        # next_id keeps incrementing past deleted ids
        n4 = add("New note", tmp)
        assert n4["id"] == 4

        print("All tests passed.")
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
