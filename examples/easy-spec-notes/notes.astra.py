#!/usr/bin/env python3
"""A small command-line notes app using notes.json in the current directory."""

import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from datetime import datetime, timezone


USAGE = (
    'Usage: python notes.py add "text" | list | done <id> | rm <id> | '
    'search <term> | stats | test'
)


class Notes:
    def __init__(self, path="notes.json"):
        self.path = Path(path)
        self.notes = []
        self.next_id = 1
        self._load()

    def _load(self):
        try:
            text = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return

        if not text.strip():
            return

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid notes file: malformed JSON") from exc

        if not isinstance(data, dict) or not isinstance(data.get("notes"), list):
            raise ValueError("Invalid notes file: expected an object with notes")

        seen = set()
        for note in data["notes"]:
            if (
                not isinstance(note, dict)
                or type(note.get("id")) is not int
                or note["id"] < 1
                or note["id"] in seen
                or not isinstance(note.get("text"), str)
                or type(note.get("done")) is not bool
                or not isinstance(note.get("created"), str)
            ):
                raise ValueError("Invalid notes file: invalid note")
            try:
                datetime.fromisoformat(note["created"])
            except ValueError as exc:
                raise ValueError("Invalid notes file: invalid timestamp") from exc
            seen.add(note["id"])

        minimum_next_id = max(seen, default=0) + 1
        next_id = data.get("next_id", minimum_next_id)
        if type(next_id) is not int or next_id < minimum_next_id:
            raise ValueError("Invalid notes file: invalid next_id")

        self.notes = data["notes"]
        self.next_id = next_id

    def _save(self):
        """Replace the data file atomically to avoid partial JSON writes."""
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix="." + self.path.name + ".",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary_path = handle.name
                json.dump(
                    {"next_id": self.next_id, "notes": self.notes},
                    handle,
                    ensure_ascii=False,
                    indent=2,
                )
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, self.path)
            temporary_path = None
        finally:
            if temporary_path is not None:
                try:
                    os.unlink(temporary_path)
                except FileNotFoundError:
                    pass

    def add(self, text):
        note = {
            "id": self.next_id,
            "text": text,
            "done": False,
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        self.next_id += 1
        self.notes.append(note)
        self._save()
        return note.copy()

    def list(self):
        return [note.copy() for note in sorted(self.notes, key=lambda n: n["id"])]

    def _find(self, note_id):
        for note in self.notes:
            if note["id"] == note_id:
                return note
        raise KeyError(note_id)

    def done(self, note_id):
        note = self._find(note_id)
        note["done"] = True
        self._save()

    def rm(self, note_id):
        note = self._find(note_id)
        self.notes.remove(note)
        self._save()

    def search(self, term):
        term = term.casefold()
        return [note for note in self.list() if term in note["text"].casefold()]

    def stats(self):
        total = len(self.notes)
        done = sum(note["done"] for note in self.notes)
        return {"total": total, "done": done, "open": total - done}


def print_notes(notes):
    if not notes:
        print("No notes.")
        return
    for note in notes:
        marker = "x" if note["done"] else " "
        print(f'{note["id"]} [{marker}] {note["text"]} ({note["created"]})')


def main(argv=None, data_path="notes.json"):
    args = list(sys.argv[1:] if argv is None else argv)
    argument_counts = {
        "add": 1,
        "list": 0,
        "done": 1,
        "rm": 1,
        "search": 1,
        "stats": 0,
        "test": 0,
    }
    if (
        not args
        or args[0] not in argument_counts
        or len(args) - 1 != argument_counts[args[0]]
    ):
        print(USAGE)
        return 2

    command = args[0]
    if command == "test":
        test()
        return 0

    note_id = None
    if command in ("done", "rm"):
        try:
            note_id = int(args[1])
            if note_id < 1:
                raise ValueError
        except ValueError:
            print("Error: id must be a positive integer.")
            print(USAGE)
            return 2

    try:
        notes = Notes(data_path)
        if command == "add":
            note = notes.add(args[1])
            print(f'Added note {note["id"]}.')
        elif command == "list":
            print_notes(notes.list())
        elif command == "done":
            notes.done(note_id)
            print(f"Marked note {note_id} as done.")
        elif command == "rm":
            notes.rm(note_id)
            print(f"Deleted note {note_id}.")
        elif command == "search":
            print_notes(notes.search(args[1]))
        elif command == "stats":
            counts = notes.stats()
            print(f'Total: {counts["total"]}')
            print(f'Done: {counts["done"]}')
            print(f'Open: {counts["open"]}')
    except KeyError:
        print(f"Error: note {note_id} not found.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


def test():
    """Exercise every command without reading or modifying real notes."""
    with tempfile.TemporaryDirectory(prefix="notes-test-") as directory:
        path = Path(directory) / "test-notes.json"

        def run(*args, expected_status=0):
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = main(args, data_path=path)
            assert status == expected_status, (args, status, stderr.getvalue())
            return stdout.getvalue(), stderr.getvalue()

        # Missing and empty files both start with no notes.
        assert Notes(path).list() == []
        assert run("list")[0] == "No notes.\n"
        assert not path.exists()
        path.write_text("", encoding="utf-8")
        assert Notes(path).stats() == {"total": 0, "done": 0, "open": 0}
        path.write_text(" \n\t", encoding="utf-8")
        assert Notes(path).list() == []

        # Each CLI invocation reloads the temporary file, testing persistence.
        assert "Added note 1." in run("add", "Buy Milk")[0]
        assert "Added note 2." in run("add", "Write Python notes")[0]
        records = Notes(path).list()
        assert [note["id"] for note in records] == [1, 2]
        assert all(note["done"] is False for note in records)
        for note in records:
            assert datetime.fromisoformat(note["created"]).tzinfo is not None

        output, _ = run("list")
        assert "1 [ ] Buy Milk" in output
        assert "2 [ ] Write Python notes" in output
        assert all(note["created"] in output for note in records)

        run("done", "1")
        assert Notes(path).list()[0]["done"] is True
        assert "1 [x] Buy Milk" in run("list")[0]
        run("done", "1")  # Marking an already-done note is harmless.

        output, _ = run("search", "mILK")
        assert "Buy Milk" in output
        assert "Write Python notes" not in output
        assert [note["id"] for note in Notes(path).search("PYTHON")] == [2]
        assert run("search", "unmatched term")[0] == "No notes.\n"

        assert run("stats")[0] == "Total: 2\nDone: 1\nOpen: 1\n"
        run("rm", "1")
        assert [note["id"] for note in Notes(path).list()] == [2]
        assert run("stats")[0] == "Total: 1\nDone: 0\nOpen: 1\n"

        # IDs remain increasing even after deleting the highest ID or all notes.
        run("rm", "2")
        assert run("stats")[0] == "Total: 0\nDone: 0\nOpen: 0\n"
        run("add", "A fresh note")
        assert Notes(path).list()[0]["id"] == 3

        for args in ((), ("unknown",), ("add",), ("done",), ("rm",), ("search",)):
            assert "Usage:" in run(*args, expected_status=2)[0]
        assert "Usage:" in run("done", "invalid", expected_status=2)[0]
        assert "not found" in run("done", "999", expected_status=1)[1]
        assert "not found" in run("rm", "999", expected_status=1)[1]

        # Corrupt data produces an error and is not silently overwritten.
        path.write_text("{broken", encoding="utf-8")
        assert "Error:" in run("add", "Do not overwrite", expected_status=1)[1]
        assert path.read_text(encoding="utf-8") == "{broken"

    print("All tests passed.")


if __name__ == "__main__":
    sys.exit(main())

