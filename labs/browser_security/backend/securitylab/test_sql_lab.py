"""Real SQLite controls and HTTP boundaries for the SQL injection lesson."""
import json
import sqlite3
from contextlib import closing
from unittest.mock import patch

from django.conf import settings
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, SimpleTestCase

from .sql_lab import FIXED_QUERY, fixture_connection


class SQLLabTests(SimpleTestCase):
    def query(self, value, mode="fixed", **extra):
        return self.client.post("/api/sql/", {"mode": mode, "input": value, **extra}, content_type="application/json")

    def test_ordinary_public_search_works_and_private_exact_search_is_empty(self):
        for mode in ("vulnerable", "fixed"):
            with self.subTest(mode=mode):
                response = self.query("Notebook", mode)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["outcome"], "read")
                self.assertEqual(response.json()["rows"], [{"id": 1, "name": "Notebook", "marker": "PUBLIC_NOTEBOOK"}])
                self.assertEqual(self.query("Private sample", mode).json()["rows"], [])
                self.assertEqual(self.query("Unknown item", mode).json()["rows"], [])

    def test_tautology_changes_structure_only_in_concatenated_query(self):
        value = "' OR 1=1 -- "
        vulnerable = self.query(value, "vulnerable").json()
        fixed = self.query(value).json()
        self.assertEqual(len(vulnerable["rows"]), 3)
        self.assertEqual(vulnerable["rows"][-1]["marker"], "PRIVATE_SQL_SENTINEL_ONLY_FOR_LAB")
        self.assertEqual(fixed["rows"], [])
        self.assertEqual(fixed["query"], FIXED_QUERY)
        self.assertEqual(fixed["parameters"], [value])
        self.assertEqual(vulnerable["parameters"], [])

    def test_parameters_preserve_legitimate_apostrophe(self):
        vulnerable = self.query("Reader's guide", "vulnerable").json()
        fixed = self.query("Reader's guide").json()
        self.assertEqual(vulnerable["outcome"], "query_error")
        self.assertEqual(vulnerable["rows"], [])
        self.assertEqual(fixed["outcome"], "read")
        self.assertEqual(fixed["rows"][0]["marker"], "PUBLIC_QUOTED_NAME")
        self.assertEqual(fixed["parameters"], ["Reader's guide"])

    def test_authorizer_blocks_mutations_files_schema_and_functions(self):
        statements = (
            "UPDATE catalog SET public=1", "DELETE FROM catalog", "DROP TABLE catalog",
            "INSERT INTO catalog VALUES (4,'x','x',1)",
            "ATTACH DATABASE ':memory:' AS other", "PRAGMA database_list",
            "SELECT name FROM sqlite_schema", "SELECT load_extension('not-a-real-extension')",
            "SELECT readfile('not-a-real-file')", "SELECT randomblob(1000000)",
        )
        for statement in statements:
            with self.subTest(statement=statement), closing(fixture_connection()) as connection:
                with self.assertRaises(sqlite3.DatabaseError):
                    connection.execute(statement)
                rows = connection.execute("SELECT id, public FROM catalog ORDER BY id").fetchall()
                self.assertEqual(rows, [(1, 1), (2, 1), (3, 0)])

    def test_multiple_statements_and_unauthorized_subqueries_fail_without_rows(self):
        for value in (
            "'; DELETE FROM catalog; -- ",
            "' UNION SELECT 1,name,sql FROM sqlite_schema -- ",
            "' UNION SELECT 1,load_extension('x'),'x' -- ",
        ):
            with self.subTest(value=value):
                result = self.query(value, "vulnerable").json()
                self.assertEqual(result["outcome"], "query_error")
                self.assertEqual(result["rows"], [])

    def test_every_request_uses_a_closed_memory_database(self):
        connect = sqlite3.connect
        connections = []

        def tracked_connect(path):
            self.assertEqual(path, ":memory:")
            connection = connect(path)
            connections.append(connection)
            return connection

        with patch("securitylab.sql_lab.sqlite3.connect", side_effect=tracked_connect):
            self.query("Notebook")
            self.query("Reader's guide", "vulnerable")
        self.assertEqual(len(connections), 2)
        for connection in connections:
            with self.assertRaises(sqlite3.ProgrammingError):
                connection.execute("SELECT 1")

    def test_progress_budget_interrupts_expensive_query(self):
        with closing(fixture_connection()) as connection:
            tables = ", ".join(f"catalog {alias}" for alias in "abcdefghij")
            order = " + ".join(f"{alias}.id" for alias in "abcdefghij")
            with self.assertRaisesRegex(sqlite3.OperationalError, "interrupted"):
                connection.execute(f"SELECT a.id FROM {tables} ORDER BY {order}").fetchall()

    def test_custom_sql_values_remain_json_serializable_and_rows_are_bounded(self):
        result = self.query("' UNION SELECT 1e999,X'00ff','TEXT_ONLY' -- ", "vulnerable").json()
        self.assertEqual(result["outcome"], "read")
        self.assertEqual(result["rows"], [{"id": "inf", "name": "hex:00ff", "marker": "TEXT_ONLY"}])
        result = self.query("' UNION ALL SELECT a.id,a.name,a.marker FROM catalog a,catalog b,catalog c -- ", "vulnerable").json()
        self.assertEqual(result["outcome"], "read")
        self.assertEqual(len(result["rows"]), 20)
        self.assertIn("first 20 rows", result["reason"])

    def test_input_validation_runs_before_opening_database(self):
        with patch("securitylab.sql_lab.fixture_connection") as connection:
            for value in ("", "a" * 257, "bad\x00value", "bad\nvalue", "\ud800", 1, None, []):
                with self.subTest(value=value):
                    response = self.query(value)
                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(response.json()["outcome"], "invalid")
            for body in ({}, [], {"mode": "fixed", "input": "Notebook", "extra": 1},
                         {"mode": "unknown", "input": "Notebook"}, {"mode": [], "input": "Notebook"}):
                response = self.client.post("/api/sql/", body, content_type="application/json")
                self.assertEqual(response.status_code, 400)
            for raw in ("{", '{"mode":"fixed","input":"Notebook","input":"x"}'):
                self.assertEqual(self.client.post("/api/sql/", raw, content_type="application/json").status_code, 400)
            connection.assert_not_called()
        self.assertEqual(self.client.post("/api/sql/", {"input": "Notebook"}).status_code, 400)
        self.assertEqual(self.client.post("/api/sql/?extra=1", {"mode": "fixed", "input": "Notebook"}, content_type="application/json").status_code, 400)
        response = self.client.get("/api/sql/")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "POST")

    def test_post_requires_csrf_token_and_allows_legitimate_same_origin_request(self):
        client = Client(enforce_csrf_checks=True)
        body = json.dumps({"mode": "fixed", "input": "Notebook"})
        self.assertEqual(client.post("/api/sql/", body, content_type="application/json").status_code, 403)
        request = RequestFactory().get("/")
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META["CSRF_COOKIE"]
        response = client.post("/api/sql/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["rows"][0]["marker"], "PUBLIC_NOTEBOOK")
        self.assertEqual(client.post("/api/sql/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token,
                                     HTTP_ORIGIN="http://untrusted.invalid").status_code, 403)
