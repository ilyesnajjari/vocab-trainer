#!/usr/bin/env python3
"""Minimal Flask web UI for the vocab trainer.

Run: FLASK_APP=vocab_trainer_web.py flask run --port 5001
or: python3 vocab_trainer_web.py
"""
from flask import Flask, request, redirect, url_for, render_template, flash, send_file, jsonify
import os
import json
from pathlib import Path
from vocab_trainer import load_words, save_words, import_text, sm2_update, match_answer, export_csv, reset_progress
from datetime import date
import random

app = Flask(__name__)
# Prefer a secret from the environment for production; fall back to a dev placeholder.
app.secret_key = os.environ.get('VOCAB_SECRET', os.environ.get('SECRET_KEY', 'change-me-insecure-dev-only'))
ROOT = Path(__file__).resolve().parent


@app.route('/')
def index():
    words = load_words()
    total = len(words)
    validated = sum(1 for w in words if w.get('status') == 'validated')
    learning = sum(1 for w in words if w.get('status') == 'learning')
    due = sum(1 for w in words if w.get('due','') <= date.today().isoformat())
    return render_template('index.html', total=total, validated=validated, learning=learning, due=due)


@app.route('/import', methods=['GET', 'POST'])
def web_import():
    if request.method == 'POST':
        # support text paste or file upload
        if 'file' in request.files and request.files['file'].filename:
            f = request.files['file']
            dest = ROOT / 'data' / f.filename
            f.save(str(dest))
            import_text(str(dest))
            flash(f'Imported {f.filename}')
            return redirect(url_for('index'))

        text = request.form.get('text', '')
        if text:
            # write to a temp file and call import_text
            p = ROOT / 'data' / 'web_upload.txt'
            p.write_text(text, encoding='utf-8')
            import_text(str(p))
            flash('Imported vocabulary successfully.')
            return redirect(url_for('index'))

    return render_template('import.html')


@app.route('/list')
def web_list():
    # Server-side search & pagination
    words = load_words()
    q = request.args.get('q','').strip().lower()
    status = request.args.get('status','').strip()
    page = int(request.args.get('page','1') or 1)
    per_page = 20

    # filter
    if q:
        filtered = [w for w in words if q in w.get('en','').lower() or q in w.get('fr','').lower()]
    else:
        filtered = words

    # filter by status if requested (e.g. ?status=learning)
    if status:
        filtered = [w for w in filtered if w.get('status') == status]

    total = len(filtered)
    page_count = max(1, (total + per_page - 1) // per_page)
    if page < 1:
        page = 1
    if page > page_count:
        page = page_count

    start = (page - 1) * per_page
    end = start + per_page
    page_items = filtered[start:end]

    # build a base query string to preserve q/status in pagination links
    parts = []
    if q:
        parts.append(f"q={q}")
    if status:
        parts.append(f"status={status}")
    base_q = ('?' + '&'.join(parts)) if parts else ''

    return render_template('list.html', words=page_items, total=total, page=page, page_count=page_count, q=q, status=status, base_q=base_q)


@app.route('/export')
def web_export():
    out = ROOT / 'data' / 'web_export.csv'
    export_csv(str(out))
    return send_file(str(out), as_attachment=True)


@app.route('/reset', methods=['POST'])
def web_reset():
    reset_progress()
    flash('Progress reset to new.')
    return redirect(url_for('index'))


@app.route('/quiz', methods=['GET'])
def web_quiz_get():
    words = load_words()
    # support query params for due_only and only_wrong
    due_only = request.args.get('due_only') == '1'
    only_wrong = request.args.get('only_wrong') == '1'
    today = date.today()
    # build candidate list based on filters
    candidates = []
    for w in words:
        if only_wrong and w.get('status') != 'learning':
            continue
        if due_only:
            try:
                due = date.fromisoformat(w.get('due'))
            except Exception:
                due = today
            if due > today:
                continue
        if w.get('status') == 'validated' and not only_wrong:
            continue
        candidates.append(w)

    if not candidates:
        flash('No items to study with current filters.')
        return redirect(url_for('index'))

    # allow showing a specific item if id provided (useful for flipping direction)
    item_id = request.args.get('id')
    dir_param = request.args.get('dir')
    if item_id:
        try:
            item_id = int(item_id)
            w = next((x for x in words if x['id'] == item_id), None)
            if not w:
                flash('Requested item not found.')
                return redirect(url_for('web_quiz_get'))
        except ValueError:
            flash('Invalid item id.')
            return redirect(url_for('web_quiz_get'))
    else:
        w = random.choice(candidates)

    # direction: use query param if provided, otherwise random
    if dir_param in ('en2fr', 'fr2en'):
        direction = dir_param
    else:
        direction = random.choice(['en2fr', 'fr2en'])

    question = w['en'] if direction == 'en2fr' else w['fr']
    return render_template('quiz.html', item=w, direction=direction, question=question, due_only=due_only, only_wrong=only_wrong)


@app.route('/quiz', methods=['POST'])
def web_quiz_post():
    words = load_words()
    wid = int(request.form.get('id'))
    direction = request.form.get('dir')
    # support actions: answer submission, show, skip
    action = request.form.get('action', 'answer')
    answer = request.form.get('answer','')
    item = next((w for w in words if w['id'] == wid), None)
    if not item:
        flash('Item not found.')
        return redirect(url_for('web_quiz_get'))

    expected = item['fr'] if direction == 'en2fr' else item['en']
    if action == 'show':
        # do not alter SRS, just show expected
        return render_template('result.html', item=item, correct=False, expected=expected, shown=True, dir=direction)
    if action == 'skip':
        # no SRS update, jump to next
        flash('Skipped')
        # preserve requested direction when skipping
        return redirect(url_for('web_quiz_get', dir=direction))

    # default: answer submission
    correct = match_answer(answer, expected)
    sm2_update(item, correct)
    save_words(words)
    # pass back the direction so result page links preserve it
    return render_template('result.html', item=item, correct=correct, expected=expected, dir=direction)


@app.route('/stats')
def web_stats():
    words = load_words()
    total = len(words)
    validated = sum(1 for w in words if w.get('status') == 'validated')
    learning = sum(1 for w in words if w.get('status') == 'learning')
    new = sum(1 for w in words if w.get('status') == 'new')
    return render_template('stats.html', total=total, validated=validated, learning=learning, new=new)


@app.route('/api/stats/status_counts')
def api_status_counts():
    """Return JSON counts by status for client-side charts."""
    words = load_words()
    counts = {'new': 0, 'learning': 0, 'validated': 0}
    for w in words:
        s = w.get('status', 'new')
        if s not in counts:
            counts[s] = 0
        counts[s] += 1
    counts['total'] = len(words)
    return jsonify(counts)


if __name__ == '__main__':
    # Determine host/port from environment (platforms like Render set $PORT)
    port = int(os.environ.get('PORT', 5001))
    host = os.environ.get('HOST', '0.0.0.0')
    # control debug via FLASK_DEBUG env (set to '0' in production)
    debug_env = os.environ.get('FLASK_DEBUG')
    debug = True if debug_env is None else (debug_env not in ('0', 'false', 'False'))
    print(f"Starting server on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)
