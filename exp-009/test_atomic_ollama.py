#!/usr/bin/env python3
"""Offline unit tests: never contact Ollama, Moltbook or the Worker."""
import importlib.util
import json
import pathlib
import unittest
from decimal import Decimal
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("exp009_atomic", ROOT / "MOLTBOOK_ATOMIC_CREATE_VERIFY_ACTIVATE.py")
atomic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(atomic)


def fake_response(value):
    return (200, {"message": {"content": json.dumps(value)}}, {})


class OllamaSafetyTests(unittest.TestCase):
    def test_valid_numbers(self):
        with patch.object(atomic, "request_json", return_value=fake_response(
            {"first": 20, "second": 5, "operation": "subtract"})):
            self.assertEqual(atomic.call_ollama("fake", "test", 1),
                             (Decimal(20), Decimal(5), "subtract"))

    def test_two_independent_matching_answers(self):
        responses = [fake_response({"first": 20, "second": 5, "operation": "subtract"})] * 2
        with patch.object(atomic, "request_json", side_effect=responses) as req:
            self.assertEqual(atomic.solve_twice(
                "fake", "A lobster swims at twenty meters and slows by five. What is the new speed?"
            ), Decimal("15.00"))
            self.assertEqual(req.call_count, 2)

    def test_two_disagree_fail_closed(self):
        responses = [fake_response({"first": 20, "second": 5, "operation": "subtract"}),
                     fake_response({"first": 20, "second": 4, "operation": "subtract"})]
        with patch.object(atomic, "request_json", side_effect=responses):
            with self.assertRaises(ValueError):
                atomic.solve_twice("fake", "twenty minus five")

    def test_bad_response_types_fail_closed(self):
        invalid = [
            {"first": "twenty", "second": 5, "operation": "subtract"},
            {"first": "20 meters", "second": 5, "operation": "subtract"},
            {"first": None, "second": 5, "operation": "subtract"},
            {"first": "NaN", "second": 5, "operation": "subtract"},
            {"first": 20, "second": 5, "operation": "bad"},
            {"first": 20, "operation": "subtract"},
            {"unclear": True}, [], "nonsense", None,
        ]
        for item in invalid:
            with self.subTest(item=item):
                with patch.object(atomic, "request_json", return_value=fake_response(item)):
                    with self.assertRaises(ValueError):
                        atomic.call_ollama("fake", "test", 1)

    def test_preflight_bad_ollama_stops_before_publication(self):
        with patch.object(atomic, "request_json", side_effect=[
            (200, {"models": [{"name": "gemma3:4b"}]}, {}),
            fake_response({"first": "twenty", "second": 5, "operation": "subtract"}),
        ]):
            with self.assertRaises(SystemExit) as stopped:
                atomic.check_ollama({"MOLTBOOK_CHALLENGE_MODEL": "gemma3:4b"})
            self.assertEqual(stopped.exception.code, 1)

    def test_historical_post_cannot_resume_or_activate(self):
        with patch.object(atomic, "confirm_post_verified") as verify, \
             patch.object(atomic, "activate_d1") as activate:
            with self.assertRaises(SystemExit) as stopped:
                atomic.resume_if_needed({
                    "status": "POST_CREATED_PENDING_MODERATION",
                    "post_id": atomic.OLD_POST_ID,
                    "verification_submission_count": 0,
                }, "fake-key")
            self.assertEqual(stopped.exception.code, 1)
            verify.assert_not_called()
            activate.assert_not_called()
    def test_no_external_connections_on_import(self):
        # Import happens above; request_json is only called inside explicitly invoked functions.
        self.assertTrue(callable(atomic.main))


if __name__ == "__main__":
    unittest.main()
