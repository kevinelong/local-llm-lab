# notes.py
import sys
import json
import os
from datetime import datetime

DATA_FILE = 'notes.json'

def load_notes():
    """Load notes from JSON file, return empty list if file doesn't exist or is invalid."""
    try:
        if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        return []
    except (json.JSONDecodeError, IOError):
        return []

def save_notes(notes):
    """Save notes to JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(notes, f, indent=2)

def add_note(text):
    """Add a new note with incrementing ID and timestamp."""
    notes = load_notes()
    new_id = max([note['id'] for note in notes], default=0) + 1
    note = {
        'id': new_id,
        'text': text,
        'done': False,
        'created': datetime.now().isoformat()
    }
    notes.append(note)
    save_notes(notes)
    print(f"Added note {new_id}")

def list_notes():
    """List all notes with status, id, text and created date."""
    notes = load_notes()
    if not notes:
        print("No notes found.")
        return
    
    for note in notes:
        status = '✓' if note['done'] else '○'
        created_date = datetime.fromisoformat(note['created']).strftime('%Y-%m-%d %H:%M')
        print(f"{status} {note['id']}: {note['text']} ({created_date})")

def done_note(note_id):
    """Mark a note as complete."""
    notes = load_notes()
    for note in notes:
        if note['id'] == note_id:
            note['done'] = True
            save_notes(notes)
            print(f"Marked note {note_id} as done")
            return
    print(f"Note {note_id} not found")

def rm_note(note_id):
    """Remove a note."""
    notes = load_notes()
    original_count = len(notes)
    notes = [note for note in notes if note['id'] != note_id]
    if len(notes) == original_count:
        print(f"Note {note_id} not found")
        return
    save_notes(notes)
    print(f"Removed note {note_id}")

def search_notes(term):
    """Search notes by text content (case-insensitive)."""
    notes = load_notes()
    matches = [note for note in notes if term.lower() in note['text'].lower()]
    if not matches:
        print("No matching notes found.")
        return
    
    for note in matches:
        status = '✓' if note['done'] else '○'
        created_date = datetime.fromisoformat(note['created']).strftime('%Y-%m-%d %H:%M')
        print(f"{status} {note['id']}: {note['text']} ({created_date})")

def stats():
    """Print statistics about notes."""
    notes = load_notes()
    total = len(notes)
    done = sum(1 for note in notes if note['done'])
    open_notes = total - done
    
    print(f"Total: {total}")
    print(f"Done: {done}")
    print(f"Open: {open_notes}")

def usage():
    """Print usage message."""
    print("Usage:")
    print("  python notes.py add \"note text\"")
    print("  python notes.py list")
    print("  python notes.py done <id>")
    print("  python notes.py rm <id>")
    print("  python notes.py search <term>")
    print("  python notes.py stats")
    print("  python notes.py test")

def test():
    """Run tests for the notes app."""
    # Use a temporary file for testing
    global DATA_FILE
    original_file = DATA_FILE
    DATA_FILE = 'test_notes.json'
    
    try:
        # Clear any existing test data
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        
        # Test add
        add_note("Test note 1")
        add_note("Test note 2")
        
        # Verify notes were added
        notes = load_notes()
        assert len(notes) == 2
        assert notes[0]['text'] == "Test note 1"
        assert notes[1]['text'] == "Test note 2"
        
        # Test done
        done_note(1)
        notes = load_notes()
        assert notes[0]['done'] == True
        
        # Test search
        search_notes("test")
        
        # Test stats
        stats()
        
        # Test rm
        rm_note(2)
        notes = load_notes()
        assert len(notes) == 1
        assert notes[0]['id'] == 1
        
        print("All tests passed!")
    finally:
        # Restore original file name and clean up
        DATA_FILE = original_file
        if os.path.exists('test_notes.json'):
            os.remove('test_notes.json')

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        usage()
        return
    
    command = sys.argv[1]
    
    if command == 'add' and len(sys.argv) >= 3:
        add_note(' '.join(sys.argv[2:]))
    elif command == 'list':
        list_notes()
    elif command == 'done' and len(sys.argv) >= 3:
        try:
            note_id = int(sys.argv[2])
            done_note(note_id)
        except ValueError:
            print("Invalid ID. Please provide a number.")
    elif command == 'rm' and len(sys.argv) >= 3:
        try:
            note_id = int(sys.argv[2])
            rm_note(note_id)
        except ValueError:
            print("Invalid ID. Please provide a number.")
    elif command == 'search' and len(sys.argv) >= 3:
        search_notes(' '.join(sys.argv[2:]))
    elif command == 'stats':
        stats()
    elif command == 'test':
        test()
    else:
        usage()

if __name__ == '__main__':
    main()
