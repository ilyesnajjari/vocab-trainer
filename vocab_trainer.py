#!/usr/bin/env python3
"""Simple vocab trainer CLI (EN <-> FR).

Usage:
  python3 vocab_trainer.py import data/words.txt
  python3 vocab_trainer.py quiz
  python3 vocab_trainer.py stats

This script stores data in ./data/words.json
"""
import argparse
import csv
import json
import os
import random
import sys
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
WORDS_JSON = DATA_DIR / "words.json"

def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def normalize(s: str) -> str:
    if s is None:
        return ""
    s = s.strip().lower()
    # remove accents
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    # collapse spaces
    return ' '.join(s.split())

def load_words():
    ensure_data_dir()
    if not WORDS_JSON.exists():
        return []
    with open(WORDS_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # ensure SRS fields exist for backwards compatibility
        for w in data:
            w.setdefault('status', 'new')
            w.setdefault('ef', 2.5)
            w.setdefault('interval', 0)
            w.setdefault('repetitions', 0)
            # due stored as ISO date string
            if 'due' not in w or not w.get('due'):
                w['due'] = date.today().isoformat()
        return data

def save_words(words):
    ensure_data_dir()
    with open(WORDS_JSON, 'w', encoding='utf-8') as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

def find_duplicate(words, en, fr):
    nen, nfr = normalize(en), normalize(fr)
    for w in words:
        if normalize(w.get('en','')) == nen and normalize(w.get('fr','')) == nfr:
            return True
    return False


def levenshtein(a: str, b: str) -> int:
    # simple iterative Levenshtein (memory optimized)
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if la == 0:
        return lb
    if lb == 0:
        return la
    prev = list(range(lb + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i] + [0] * lb
        for j, cb in enumerate(b, start=1):
            ins = curr[j-1] + 1
            dele = prev[j] + 1
            sub = prev[j-1] + (0 if ca == cb else 1)
            curr[j] = min(ins, dele, sub)
        prev = curr
    return prev[lb]


def similar_enough(given: str, expected: str) -> bool:
    # allow small typos: threshold = 30% of length
    g = normalize(given)
    e = normalize(expected)
    # consider comma-separated alternatives
    for alt in [a.strip() for a in expected.split(',')]:
        alt_n = normalize(alt)
        if not alt_n:
            continue
        if g == alt_n:
            return True
        d = levenshtein(g, alt_n)
        thr = max(1, int(len(alt_n) * 0.3))
        if d <= thr:
            return True
    return False

def import_text(filepath: str):
    path = Path(filepath)
    if not path.exists():
        print(f"File not found: {filepath}")
        return
    words = load_words()
    added = 0
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # split on first ':'
            if ':' not in line:
                print(f"Skipping (no ':'): {line}")
                continue
            left, right = line.split(':', 1)
            en = left.strip()
            fr = right.strip()
            if not en or not fr:
                print(f"Skipping (empty side): {line}")
                continue
            if find_duplicate(words, en, fr):
                continue
            entry = {"id": len(words)+1, "en": en, "fr": fr, "status": "new"}
            words.append(entry)
            added += 1
    save_words(words)
    print(f"Imported {added} entries. Total now: {len(words)}")

def stats():
    words = load_words()
    total = len(words)
    validated = sum(1 for w in words if w.get('status') == 'validated')
    new = sum(1 for w in words if w.get('status') == 'new')
    learning = total - validated - new
    print(f"Total: {total}  Validated: {validated}  New: {new}  Learning: {learning}")

def match_answer(given: str, expected: str) -> bool:
    # Use permissive matching (normalization + levenshtein tolerance)
    return similar_enough(given, expected)


def sm2_update(item: dict, correct: bool):
    # implement simplified SM-2 algorithm
    # fields: ef (float), interval (days int), repetitions (int), due (ISO date)
    ef = float(item.get('ef', 2.5))
    interval = int(item.get('interval', 0))
    reps = int(item.get('repetitions', 0))
    today = date.today()
    if correct:
        quality = 5  # since input is binary, assume perfect when correct
        reps += 1
        if reps == 1:
            interval = 1
        elif reps == 2:
            interval = 6
        else:
            interval = max(1, round(interval * ef))
        # update ef
        ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        if ef < 1.3:
            ef = 1.3
    else:
        # wrong answer: reset repetitions
        reps = 0
        interval = 1
        quality = 2
        ef = max(1.3, ef - 0.2)
    item['ef'] = round(ef, 2)
    item['interval'] = int(interval)
    item['repetitions'] = int(reps)
    item['due'] = (today + timedelta(days=interval)).isoformat()
    # status update
    if correct:
        item['status'] = 'validated' if reps >= 3 else 'learning'
    else:
        item['status'] = 'learning'


def quiz_loop(due_only=False, only_wrong=False):
    words = load_words()
    if not words:
        print("No words loaded. Import a file first.")
        return
    today = date.today()
    # select pool based on flags
    pool = []
    for w in words:
        if only_wrong and w.get('status') != 'learning':
            continue
        if due_only:
            try:
                due = datetime.fromisoformat(w.get('due')).date()
            except Exception:
                due = today
            if due > today:
                continue
        if w.get('status') == 'validated' and not only_wrong:
            # still allow validated words if only_wrong not set
            continue
        pool.append(w)

    if not pool:
        print("No items to study based on the selected filters.")
        return

    random.shuffle(pool)
    print("Starting quiz. Type :exit to quit, :skip to requeue, :show to reveal, :stats for progress.")
    while pool:
        w = pool.pop(0)
        direction = random.choice(['en2fr', 'fr2en'])
        if direction == 'en2fr':
            prompt = f"Translate to French: {w['en']}\n> "
            expected = w['fr']
        else:
            prompt = f"Translate to English: {w['fr']}\n> "
            expected = w['en']

        answer = input(prompt).strip()
        if not answer:
            print("(empty) — requeued")
            pool.append(w)
            continue
        if answer.lower() in (':exit', ':quit'):
            break
        if answer.lower() == ':skip':
            pool.append(w)
            continue
        if answer.lower() == ':show':
            print(f"Answer: {expected}")
            pool.append(w)
            continue
        if answer.lower() == ':stats':
            stats()
            pool.append(w)
            continue

        correct = match_answer(answer, expected)
        if correct:
            print("Correct! ✅")
        else:
            print(f"Wrong — expected: {expected}")

        # update SRS and statuses
        sm2_update(w, correct)
        # persist
        save_words(words)

        # if wrong, requeue
        if not correct:
            pool.append(w)

    print("Quiz ended. Saving progress.")
    save_words(words)

def list_words():
    words = load_words()
    for w in words:
        print(f"{w['id']:3d} | {w['en']}  —  {w['fr']}  [{w.get('status')}] due:{w.get('due')} ef:{w.get('ef')} int:{w.get('interval')} rep:{w.get('repetitions')}")


def import_csv(filepath: str):
    path = Path(filepath)
    if not path.exists():
        print(f"File not found: {filepath}")
        return
    words = load_words()
    added = 0
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            en = row.get('en') or row.get('english') or row.get('English') or ''
            fr = row.get('fr') or row.get('french') or row.get('French') or ''
            if not en or not fr:
                continue
            if find_duplicate(words, en, fr):
                continue
            entry = {"id": len(words)+1, "en": en.strip(), "fr": fr.strip(), 'status': 'new', 'ef': 2.5, 'interval': 0, 'repetitions': 0, 'due': date.today().isoformat()}
            words.append(entry)
            added += 1
    save_words(words)
    print(f"Imported {added} entries from CSV. Total now: {len(words)}")


def export_csv(filepath: str):
    words = load_words()
    path = Path(filepath)
    with open(path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'en', 'fr', 'status', 'ef', 'interval', 'repetitions', 'due']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for w in words:
            writer.writerow({k: w.get(k, '') for k in fieldnames})
    print(f"Exported {len(words)} entries to {filepath}")

def reset_progress():
    words = load_words()
    for w in words:
        w['status'] = 'new'
    save_words(words)
    print("All words reset to 'new'.")

def main():
    parser = argparse.ArgumentParser(description='Vocab Trainer CLI')
    sub = parser.add_subparsers(dest='cmd')
    imp = sub.add_parser('import', help='Import vocabulary from text file')
    imp.add_argument('file')
    sub.add_parser('import_csv', help='Import vocabulary from CSV file')
    exp = sub.add_parser('export_csv', help='Export vocabulary to CSV file')
    exp.add_argument('file')
    quiz = sub.add_parser('quiz', help='Start interactive quiz')
    quiz.add_argument('--due-only', action='store_true', help='Only quiz items due today or earlier')
    quiz.add_argument('--only-wrong', action='store_true', help='Only quiz items marked as learning')
    sub.add_parser('stats', help='Show statistics')
    sub.add_parser('list', help='List all words')
    sub.add_parser('reset', help='Reset all statuses to new')

    args = parser.parse_args()
    if args.cmd == 'import':
        import_text(args.file)
    elif args.cmd == 'import_csv':
        parser = argparse.ArgumentParser()
        parser.add_argument('file')
        parsed = parser.parse_args(sys.argv[2:])
        import_csv(parsed.file)
    elif args.cmd == 'export_csv':
        export_csv(args.file)
    elif args.cmd == 'quiz':
        # pass flags to quiz_loop
        # args may contain due_only and only_wrong
        due_only = getattr(args, 'due_only', False)
        only_wrong = getattr(args, 'only_wrong', False)
        quiz_loop(due_only=due_only, only_wrong=only_wrong)
    elif args.cmd == 'stats':
        stats()
    elif args.cmd == 'list':
        list_words()
    elif args.cmd == 'reset':
        reset_progress()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
