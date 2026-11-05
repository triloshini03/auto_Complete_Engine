"""Unit and API tests for the Smart Autocomplete Engine."""

import json
import tempfile
import unittest
from pathlib import Path

from backend.app import create_app, load_dataset
from backend.history import SearchHistory
from backend.ranking import rank_suggestions
from backend.suggestion_engine import SuggestionEngine
from backend.trie import Trie


class TrieTests(unittest.TestCase):
    def setUp(self):
        self.trie = Trie()
        for word in ("python", "pyramid", "javascript"):
            self.trie.insert(word)

    def test_insert_and_exact_search(self):
        self.assertTrue(self.trie.search("PYTHON"))
        self.assertFalse(self.trie.search("py"))
        self.assertFalse(self.trie.search(""))

    def test_prefix_search_returns_sorted_words(self):
        self.assertTrue(self.trie.starts_with("py"))
        self.assertEqual(self.trie.words_with_prefix("py"), ["pyramid", "python"])
        self.assertEqual(self.trie.words_with_prefix("unknown"), [])

    def test_invalid_insert_and_search_inputs(self):
        with self.assertRaises(ValueError):
            self.trie.insert("  ")
        with self.assertRaises(TypeError):
            self.trie.insert(None)
        with self.assertRaises(TypeError):
            self.trie.search(None)


class RankingTests(unittest.TestCase):
    def test_frequency_and_history_improve_rank(self):
        ranked = rank_suggestions(
            {"python basics": "prefix", "python guide": "prefix"},
            "python",
            {"python basics": 10, "python guide": 100},
            {"python basics": 20, "python guide": 0},
            limit=2,
        )
        self.assertEqual(ranked[0]["query"], "python basics")
        self.assertEqual(ranked[0]["source"], "prefix")


class SuggestionEngineTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.history = SearchHistory(
            Path(self.temporary_directory.name) / "history.json"
        )
        self.engine = SuggestionEngine(
            [
                {"query": "python programming", "frequency": 100},
                {"query": "python tutorial", "frequency": 50},
                {"query": "javascript tutorial", "frequency": 80},
            ],
            self.history,
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_prefix_autocomplete_and_ranking(self):
        suggestions = self.engine.suggest("py")
        self.assertEqual(
            {item["query"] for item in suggestions},
            {"python programming", "python tutorial"},
        )
        self.assertGreater(
            suggestions[0]["score"],
            next(item["score"] for item in suggestions if item["query"] == suggestions[1]["query"])
            if len(suggestions) > 1
            else 0,
        )

    def test_typo_tolerance(self):
        suggestions = self.engine.suggest("pythn")
        self.assertEqual(suggestions[0]["query"], "python programming")
        self.assertEqual(suggestions[0]["source"], "typo")

    def test_history_terms_are_suggested_and_boosted(self):
        self.history.record("python personal project")
        suggestions = self.engine.suggest("python")
        self.assertIn("python personal project", {item["query"] for item in suggestions})
        self.assertEqual(
            next(item for item in suggestions if item["query"] == "python personal project")[
                "source"
            ],
            "history",
        )

    def test_empty_and_invalid_queries(self):
        self.assertEqual(self.engine.suggest("  "), [])
        with self.assertRaises(TypeError):
            self.engine.suggest(None)
        with self.assertRaises(ValueError):
            self.engine.suggest("python", limit=0)


class FlaskApiTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.app = create_app(Path(self.temporary_directory.name) / "history.json")
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_dataset_has_at_least_one_hundred_terms(self):
        dataset = load_dataset(Path(__file__).resolve().parents[1] / "backend" / "dataset.json")
        self.assertGreaterEqual(len(dataset), 100)

    def test_autocomplete_empty_input_and_invalid_input(self):
        response = self.client.get("/api/autocomplete")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["suggestions"], [])

        too_long = self.client.get(f"/api/autocomplete?q={'a' * 101}")
        self.assertEqual(too_long.status_code, 400)
        self.assertIn("error", too_long.get_json())

    def test_search_records_recent_history_and_clear_removes_it(self):
        invalid = self.client.post("/api/search", json={"query": "  "})
        self.assertEqual(invalid.status_code, 400)

        response = self.client.post("/api/search", json={"query": "python programming"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["query"], "python programming")
        self.assertEqual(
            self.client.get("/api/history").get_json()["searches"][0]["query"],
            "python programming",
        )

        cleared = self.client.delete("/api/history")
        self.assertEqual(cleared.status_code, 200)
        self.assertEqual(self.client.get("/api/history").get_json()["searches"], [])

    def test_rejects_malformed_search_payload(self):
        response = self.client.post(
            "/api/search",
            data=json.dumps(["not", "an", "object"]),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_frontend_and_popular_endpoint_are_served(self):
        index_response = self.client.get("/")
        self.assertEqual(index_response.status_code, 200)
        index_response.close()
        popular = self.client.get("/api/popular")
        self.assertEqual(popular.status_code, 200)
        self.assertTrue(popular.get_json()["suggestions"])


if __name__ == "__main__":
    unittest.main()
