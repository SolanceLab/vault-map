# vault-map from Python, and how notes are scored

## Importable functions

| Function | What it does |
|---|---|
| `search(terms, vault, top_n)` | Importable. Returns the `query` results as a dict and prints nothing |
| `search_sections(terms, vault, top_n)` | Importable. Section search: returns the best passages, each with the note it came from |

Load the file as a module (it is one file, `vault-map.py`); the example in [section-search.md](section-search.md) shows how.

## Scoring

Note scoring: title match 5, tag match 3, heading match 2, path match 1, plus up to 10 for body occurrences. Bodies are scanned live at query time (about 1 second across 800 notes).
