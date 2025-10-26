```markdown
# Vocab Trainer

Simple command-line vocabulary trainer (English ↔ French).

Features:
- Import vocabulary from a text file with lines in the format: `English : French` (colon separator).
- Quiz you randomly, alternating direction (EN→FR or FR→EN).
- Wrong answers are requeued for later; correct answers are marked validated.
- Progress is saved to `data/words.json` and uses a simple SM-2-like spaced repetition schedule (ef, interval, repetitions, due date).
- Fuzzy matching (Levenshtein tolerance) allows small typos.

Getting started

1. Import the sample vocabulary:

```bash
python3 vocab_trainer.py import data/words.txt
```

2. Start a quiz:

```bash
python3 vocab_trainer.py quiz
```

Advanced options

- Quiz only due items:

```bash
python3 vocab_trainer.py quiz --due-only
```

- Quiz only learning (wrong) items:

```bash
python3 vocab_trainer.py quiz --only-wrong
```

Import/export CSV:

```bash
python3 vocab_trainer.py import_csv file.csv
python3 vocab_trainer.py export_csv out.csv
```

Web UI

Start a minimal web UI (requires Flask installed):

```bash
pip install -r requirements.txt
python3 vocab_trainer_web.py
# then open http://127.0.0.1:5001
```

Commands available during quiz (type them instead of an answer):
- `:exit` or `:quit` — quit quiz
- `:skip` — skip and requeue
- `:show` — reveal the correct answer
- `:stats` — show progress counts

Files
- `vocab_trainer.py` — main script
- `vocab_trainer_web.py` — minimal Flask web UI
- `data/words.txt` — sample vocabulary to import
- `data/words.json` — stored progress and word list (created after import)
- `requirements.txt` — web UI dependencies (Flask)

This tool runs with Python 3.8+. The web UI requires Flask.

Enjoy!

```
