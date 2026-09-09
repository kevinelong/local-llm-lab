"""A small command-line notes app using only the Python standard library."""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile


class Notes:
    def __init__(self, data_file="notes.json"):
        self.data_file = Path(data_file)
        self.notes = []
        self.next_id = 1
        self.load()

    def load(self):
        try:
            content = self.data_file.read_text(encoding="utf-8")
        except FileNotFoundError:
            return
        if not content.strip():
            return
        data = json.loads(content)
        if (not isinstance(data, dict)
                or not isinstance(data.get("notes"), list)
                or type(data.get("next_id")) is not int
                or data["next_id"] < 1):
            raise ValueError("Invalid notes file format.")
        seen_ids = set()
        for note in data["notes"]:
            if (not isinstance(note, dict)
                    or type(note.get("id")) is not int
                    or note["id"] < 1
                    or note["id"] in seen_ids
                    or not isinstance(note.get("text"), str)
                    or type(note.get("done")) is not bool
                    or not isinstance(note.get("created"), str)):
                raise ValueError("Invalid note in notes file.")
            seen_ids.add(note["id"])
        if data["next_id"] <= max(seen_ids, default=0):
            raise ValueError("Invalid next id in notes file.")
        self.notes = data["notes"]
        self.next_id = data["next_id"]

    def save(self):
        data = {"next_id": self.next_id, "notes": self.notes}
        temporary_path = None
        try:
            with NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.data_file.parent,
                prefix=self.data_file.name + ".", suffix=".tmp", delete=False
            ) as stream:
                temporary_path = Path(stream.name)
                json.dump(data, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            os.replace(temporary_path, self.data_file)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

    def add(self, text):
        note = {
            "id": self.next_id,
            "text": text,
            "done": False,
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        self.notes.append(note)
        self.next_id += 1
        self.save()
        return note

    def list_notes(self):
        return list(self.notes)

    def done(self, note_id):
        for note in self.notes:
            if note["id"] == note_id:
                note["done"] = True
                self.save()
                return note
        raise ValueError("No note with id {}.".format(note_id))

    def rm(self, note_id):
        for index, note in enumerate(self.notes):
            if note["id"] == note_id:
                removed = self.notes.pop(index)
                self.save()
                return removed
        raise ValueError("No note with id {}.".format(note_id))

    def search(self, term):
        term = term.casefold()
        return [note for note in self.notes if term in note["text"].casefold()]

    def stats(self):
        total = len(self.notes)
        done = sum(note["done"] for note in self.notes)
        return {"total": total, "done": done, "open": total - done}


def print_notes(notes):
    for note in notes:
        marker = "[x]" if note["done"] else "[ ]"
        print("{} {} {} ({})".format(
            note["id"], marker, note["text"], note["created"]
        ))


def test():
    """Exercise the commands against a temporary file, leaving real notes alone."""
    from contextlib import redirect_stderr, redirect_stdout
    from io import StringIO
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        data_file = Path(directory) / "notes.json"

        def run(*arguments, expected_code=0):
            stdout, stderr = StringIO(), StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                try:
                    code = main(list(arguments), data_file=data_file)
                except SystemExit as exc:
                    code = exc.code
            assert code == expected_code, (arguments, code, stderr.getvalue())
            if expected_code == 0:
                assert stderr.getvalue() == "", stderr.getvalue()
            return stdout.getvalue(), stderr.getvalue()

        assert run("list")[0] == ""
        assert run("stats")[0] == "Total: 0\nDone: 0\nOpen: 0\n"
        assert not data_file.exists()
        for empty in ("", " \n\t"):
            data_file.write_text(empty, encoding="utf-8")
            assert run("list")[0] == ""

        assert run("add", "Buy MILK")[0] == "Added note 1.\n"
        assert run("add", "Read a book")[0] == "Added note 2.\n"
        saved = json.loads(data_file.read_text(encoding="utf-8"))
        assert saved["next_id"] == 3
        assert [note["id"] for note in saved["notes"]] == [1, 2]
        assert all(note["done"] is False for note in saved["notes"])
        for note in saved["notes"]:
            assert datetime.fromisoformat(note["created"]).tzinfo is not None
        created = saved["notes"][0]["created"]
        listing = run("list")[0]
        assert "1 [ ] Buy MILK ({})\n".format(created) in listing
        assert "2 [ ] Read a book (" in listing

        assert run("done", "1")[0] == "Completed note 1.\n"
        run("done", "1")
        completed_line = "1 [x] Buy MILK ({})\n".format(created)
        assert completed_line in run("list")[0]
        assert run("search", "mIlK")[0] == completed_line
        assert run("search", "absent")[0] == ""
        assert run("search", "")[0] == run("list")[0]
        assert run("stats")[0] == "Total: 2\nDone: 1\nOpen: 1\n"

        assert run("rm", "2")[0] == "Deleted note 2.\n"
        assert run("list")[0] == completed_line
        assert run("add", "Visit the caf\u00e9")[0] == "Added note 3.\n"
        assert "Visit the caf\u00e9" in run("search", "CAF\u00c9")[0]
        assert run("stats")[0] == "Total: 2\nDone: 1\nOpen: 1\n"

        unchanged = data_file.read_bytes()
        for command in ("done", "rm"):
            assert "No note with id 999" in run(
                command, "999", expected_code=1
            )[1]
        for arguments in (
            (), ("unknown",), ("add",), ("done",), ("rm",), ("search",),
            ("done", "bad-id"), ("rm", "bad-id"), ("list", "extra"),
        ):
            assert "usage:" in run(*arguments, expected_code=2)[1].lower()
        assert data_file.read_bytes() == unchanged

        run("rm", "1")
        run("rm", "3")
        assert run("list")[0] == ""
        assert run("stats")[0] == "Total: 0\nDone: 0\nOpen: 0\n"
        assert run("add", "After deleting all notes")[0] == "Added note 4.\n"

        data_file.write_text("invalid json", encoding="utf-8")
        assert "error:" in run("add", "Do not overwrite", expected_code=1)[1]
        assert data_file.read_text(encoding="utf-8") == "invalid json"

    print("All tests passed.")


def main(argv=None, data_file="notes.json"):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    add_parser = commands.add_parser("add", help="add a note")
    add_parser.add_argument("text")
    commands.add_parser("list", help="list all notes")
    done_parser = commands.add_parser("done", help="mark a note complete")
    done_parser.add_argument("id", type=int)
    rm_parser = commands.add_parser("rm", help="delete a note")
    rm_parser.add_argument("id", type=int)
    search_parser = commands.add_parser("search", help="search note text")
    search_parser.add_argument("term")
    commands.add_parser("stats", help="show total, done, and open counts")
    commands.add_parser("test", help="run tests using a temporary data file")
    args = parser.parse_args(argv)

    if args.command == "test":
        test()
        return 0

    try:
        notes = Notes(data_file)
        if args.command == "add":
            note = notes.add(args.text)
            print("Added note {}.".format(note["id"]))
        elif args.command == "list":
            print_notes(notes.list_notes())
        elif args.command == "done":
            notes.done(args.id)
            print("Completed note {}.".format(args.id))
        elif args.command == "rm":
            notes.rm(args.id)
            print("Deleted note {}.".format(args.id))
        elif args.command == "search":
            print_notes(notes.search(args.term))
        elif args.command == "stats":
            counts = notes.stats()
            print("Total: {total}\nDone: {done}\nOpen: {open}".format(**counts))
    except (OSError, ValueError) as exc:
        parser.exit(1, "error: {}\n".format(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
