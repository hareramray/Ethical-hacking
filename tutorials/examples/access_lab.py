"""Synthetic authorization model plus an optional loopback HTTP demonstration.

No real authentication: fixed training tokens are public fixtures.
python tutorials/examples/access_lab.py --serve
"""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

TOKENS = {'alice-lab': 'alice', 'bob-lab': 'bob'}
NOTES = {'n1': {'owner': 'alice', 'text': 'Synthetic Alice note'},
         'n2': {'owner': 'bob', 'text': 'Synthetic Bob note'}}


def read_note(identity, note_id, *, enforce_owner=True):
    if identity not in TOKENS.values():
        return 401, {'error': 'authentication required'}
    note = NOTES.get(note_id)
    if note is None:
        return 404, {'error': 'not found'}
    if enforce_owner and note['owner'] != identity:
        return 403, {'error': 'forbidden'}
    return 200, dict(note)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        token = self.headers.get('Authorization', '').removeprefix('Bearer ')
        identity = TOKENS.get(token)
        if self.path.startswith('/notes/'):
            status, result = read_note(identity, self.path[len('/notes/'):])
        else:
            status, result = 404, {'error': 'not found'}
        body = json.dumps(result).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Do not record tokens or personal data. Only synthetic request summaries.
        print('LAB HTTP:', format % args)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--serve', action='store_true')
    args = parser.parse_args()
    if args.serve:
        with HTTPServer(('127.0.0.1', 8765), Handler) as server:
            print('Synthetic API: http://127.0.0.1:8765/notes/n1 ; Ctrl+C to stop')
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
    else:
        for enforce in (False, True):
            for user, item in [('alice', 'n1'), ('bob', 'n1'), (None, 'n1')]:
                status, _ = read_note(user, item, enforce_owner=enforce)
                print(f'owner_check={enforce} identity={user} note={item} -> {status}')


if __name__ == '__main__':
    main()
