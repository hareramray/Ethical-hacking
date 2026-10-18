"""Correlate synthetic denied-then-allowed reads, not a production detector."""
from datetime import datetime
import json
from pathlib import Path


def timestamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def load_events():
    return [json.loads(line) for line in Path(__file__).with_name('events.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]


def detect(events):
    denied = {}
    matches = []
    for event in sorted(events, key=lambda e: timestamp(e['event_time'])):
        if event.get('kind') != 'document_read':
            continue
        key = (event.get('actor_id'), event.get('session_id'), event.get('document'))
        if any(value is None for value in key):
            continue
        time = timestamp(event['event_time'])
        if event.get('outcome') == 'denied':
            denied[key] = (time, event['id'])
        elif event.get('outcome') == 'allowed' and key in denied:
            previous, previous_id = denied[key]
            if 0 <= (time - previous).total_seconds() <= 120:
                matches.append((previous_id, event['id']))
    return matches


if __name__ == '__main__':
    events = load_events()
    for event in sorted(events, key=lambda e: timestamp(e['event_time'])):
        print(event['event_time'], event['id'], event['kind'])
    print('Review pairs:', detect(events))
    print('A match is a review hypothesis; legitimate permission changes can explain it.')
