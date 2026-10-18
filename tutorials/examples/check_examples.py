"""Meaningful behavior checks for the supplied portable teaching fixtures."""
from http.server import HTTPServer
import json
from threading import Thread
import unittest
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError

from access_lab import Handler, read_note
from analyze_events import detect, load_events
from parser_lab import corpus, parse_checked, parse_naive


class Examples(unittest.TestCase):
    def test_authorization_and_regression(self):
        self.assertEqual(read_note('bob', 'n1', enforce_owner=False)[0], 200)
        self.assertEqual(read_note('bob', 'n1')[0], 403)
        self.assertEqual(read_note('alice', 'n1')[0], 200)
        self.assertEqual(read_note(None, 'n1')[0], 401)
        self.assertEqual(read_note('alice', 'absent')[0], 404)

    def test_http_boundary(self):
        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        opener = build_opener(ProxyHandler({}))
        try:
            url = f'http://127.0.0.1:{server.server_port}/notes/n1'
            for token, expected in [('alice-lab', 200), ('bob-lab', 403), ('unknown', 401)]:
                request = Request(url, headers={'Authorization': 'Bearer ' + token})
                try:
                    response = opener.open(request, timeout=3)
                except HTTPError as error:
                    response = error
                with response:
                    self.assertEqual(response.status, expected)
                    body = json.load(response)
                    self.assertEqual('text' in body, expected == 200)
        finally:
            server.shutdown()
            thread.join(timeout=3)
            server.server_close()

    def test_correlation_and_near_name(self):
        events = load_events()
        self.assertEqual(detect(list(reversed(events))), [('E3', 'E5')])
        self.assertEqual(detect([e for e in events if e['id'] != 'E5']), [])
        delayed = [dict(e) for e in events]
        next(e for e in delayed if e['id'] == 'E5')['event_time'] = '2026-10-18T04:04:01Z'
        self.assertEqual(detect(delayed), [])

    def test_parser_boundaries_and_corpus(self):
        with self.assertRaises(IndexError):
            parse_naive(b'\x05abc')
        self.assertEqual(parse_checked(b'\x03abc'), b'abc')
        self.assertEqual(parse_checked(b'\x00'), b'')
        for data in corpus():
            valid = bool(data) and data[0] <= 32 and len(data) == data[0] + 1
            if valid:
                self.assertEqual(parse_checked(data), data[1:])
            else:
                with self.assertRaises(ValueError):
                    parse_checked(data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
