"""Flask application for the Smart Autocomplete Engine."""

import json
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from .history import SearchHistory
from .suggestion_engine import SuggestionEngine

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
MAX_QUERY_LENGTH = 100


def load_dataset(path):
    """Load and validate the JSON suggestion dataset."""
    with Path(path).open("r", encoding="utf-8") as dataset_file:
        entries = json.load(dataset_file)
    if not isinstance(entries, list):
        raise ValueError("dataset.json must contain a JSON list")

    for index, entry in enumerate(entries):
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("query"), str)
            or not entry["query"].strip()
            or not isinstance(entry.get("frequency", 0), int)
        ):
            raise ValueError(f"dataset entry {index} has an invalid shape")
    return entries


def create_app(history_path=None):
    """Create the Flask app and its suggestion engine."""
    app = Flask(
        __name__,
        static_folder=str(FRONTEND_DIR),
        static_url_path="/static",
    )
    history = SearchHistory(
        history_path or BACKEND_DIR / "search_history.json"
    )
    engine = SuggestionEngine(load_dataset(BACKEND_DIR / "dataset.json"), history)
    app.config["SEARCH_HISTORY"] = history
    app.config["SUGGESTION_ENGINE"] = engine

    @app.get("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.get("/api/autocomplete")
    def autocomplete():
        query = request.args.get("q", "")
        if len(query) > MAX_QUERY_LENGTH:
            return jsonify({"error": "Search query must be 100 characters or fewer."}), 400
        try:
            suggestions = engine.suggest(query)
        except (TypeError, ValueError) as error:
            return jsonify({"error": str(error)}), 400
        return jsonify({"query": query, "suggestions": suggestions})

    @app.get("/api/popular")
    def popular():
        return jsonify({"suggestions": engine.popular()})

    @app.get("/api/history")
    def recent_searches():
        try:
            return jsonify({"searches": history.recent()})
        except (OSError, ValueError, json.JSONDecodeError):
            app.logger.exception("Unable to read search history")
            return jsonify({"error": "Search history could not be read."}), 500

    @app.post("/api/search")
    def search():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or not isinstance(payload.get("query"), str):
            return jsonify({"error": "Request body must include a string query."}), 400

        query = payload["query"].strip()
        if not query:
            return jsonify({"error": "Search query cannot be empty."}), 400
        if len(query) > MAX_QUERY_LENGTH:
            return jsonify({"error": "Search query must be 100 characters or fewer."}), 400
        try:
            entry = history.record(query)
        except (OSError, ValueError) as error:
            app.logger.exception("Unable to save search history")
            return jsonify({"error": f"Search could not be saved: {error}"}), 500
        return jsonify({"query": query, "searched_at": entry["searched_at"]})

    @app.delete("/api/history")
    def clear_history():
        try:
            history.clear()
        except OSError as error:
            app.logger.exception("Unable to clear search history")
            return jsonify({"error": f"Search history could not be cleared: {error}"}), 500
        return jsonify({"message": "Search history cleared.", "searches": []})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
