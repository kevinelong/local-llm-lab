# Spec: "notes" - a small command-line notes app

Build a single file `notes.py` in Python (standard library only) that meets ALL of the following
requirements. Work through them incrementally, one at a time.

1. `python notes.py add "some text"` - add a note. Assign an incrementing integer id and store a created
   timestamp.
2. `python notes.py list` - list all notes showing id, a done marker, the text, and the created date.
3. `python notes.py done <id>` - mark the note with that id as complete.
4. `python notes.py rm <id>` - delete the note with that id.
5. `python notes.py search <term>` - list notes whose text contains term (case-insensitive).
6. Persist all notes to `notes.json` in the current directory. Load on startup. Handle a missing or empty
   file gracefully (start with no notes, no crash).
7. `python notes.py stats` - print total notes, number done, and number open.

Also:
- For an unknown command or missing arguments, print a short usage message.
- Include a `test()` function (run via `python notes.py test`) that exercises add, list, done, rm, search,
  and stats with asserts, using a temporary data file so it does not clobber real notes.
