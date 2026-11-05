# Smart Autocomplete Engine

A small, full-stack search suggestion app built with Python, Flask, a Trie, HTML, CSS, JavaScript, and JSON. Suggestions appear as you type, account for small spelling mistakes, and improve using local search history.

## Features

- Instant prefix matching backed by a Trie.
- Typo-tolerant suggestions for short edit-distance matches.
- Ranking informed by dataset frequency and searches made in this browser session.
- Popular searches and recent searches, persisted to a local JSON file.
- Clear the input or delete saved search history.
- Choose suggestions by mouse, keyboard, or the search button.
- Responsive interface with keyboard navigation and accessible status messages.
- Input validation and JSON error responses on the API.

## Requirements

- Python 3.9 or newer.
- `pip`.

## Install and run

Run these commands from the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m backend.app
```

On Windows PowerShell, activate the environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

The Flask server starts on `http://127.0.0.1:5000`. Open that address in a browser to use the app. Keep the terminal running while you use it; press `Ctrl+C` to stop the server.

## Run tests

From the project root, with the virtual environment active:

```bash
python -m unittest discover -s tests -v
```

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/autocomplete?q=python` | Return ranked prefix, history, and typo suggestions |
| `GET` | `/api/popular` | Return the most popular dataset terms |
| `GET` | `/api/history` | Return unique recent searches |
| `POST` | `/api/search` | Record a query; JSON body: `{"query": "python"}` |
| `DELETE` | `/api/history` | Clear the saved search history |

Searches are stored locally in `backend/search_history.json` when the app is run. The file is created automatically and excluded from version control.

## Project architecture

```text
auto-complete-engine/
├── backend/
│   ├── app.py                 # Flask routes and application factory
│   ├── dataset.json           # 100+ searchable sample queries
│   ├── history.py             # Atomic JSON-backed recent-search storage
│   ├── ranking.py             # Relevance, frequency, and history scoring
│   ├── suggestion_engine.py   # Trie lookup and typo-tolerant suggestions
│   └── trie.py                # Prefix-search data structure
├── frontend/
│   ├── index.html             # Accessible search interface
│   ├── script.js              # API requests and interactive behavior
│   └── style.css              # Responsive layout and visual design
├── tests/
│   └── test_autocomplete.py   # Trie, ranking, engine, and API tests
├── requirements.txt
└── README.md
```

## Screenshots

Add screenshots of the running application here. For example:

```md
![Smart Autocomplete Engine desktop view](screenshots/desktop.png)
![Smart Autocomplete Engine mobile view](screenshots/mobile.png)
```

## Notes

- The sample frequency values are illustrative ranking signals, not live search analytics.
- Search history is local to this running app instance and is not associated with individual user accounts.
- Google Fonts are used when available; the page falls back to system sans-serif fonts when offline.
