# Changelog

## 1.4.0

Installable as a plugin for Claude Code and Codex. The plugin is a skill that runs vault-map with `uvx` straight from this repository, so nothing is copied by hand. `pyproject.toml` lets `uvx` fetch the one script. The tool itself is unchanged.

## 1.3.1

The copyright line at the top of each file now names this project and its licence (PolyForm Noncommercial 1.0.0); the earlier line wrongly reserved every right, which the licence does not. No code changes.

## [1.3.0]

### Added
- Section search: `search_sections(terms, vault, top_n)` ranks the sections of your notes, so the passage that answers a question comes back, not only the note around it. Same result shape as `search()`, plus three fields: `section` (the heading), `text` (the section text) and `also_in` (other notes carrying the same passage).
- `vault-map.py query "terms" --sections` (with `--n` and `--json`) runs section search from the command line.
- A saved section index, `section_index`, kept in `~/.cache/vault-map` (never inside the vault). Only changed notes are re-read.
- Sentence-boundary snippets, cut around the best-matching window.
- A passage copied across notes is shown once; the other copies are listed in `also_in`.
- `tests/` (standard-library `unittest`, no network, cache kept in a temp directory) and `make test`.
- CONTRACT.md and NOTICE.md.

### Changed
- Licence: this version and later are PolyForm Noncommercial 1.0.0 with a Required Notice (see LICENSE.md and NOTICE.md). Copies of vault-map 1.2.0 and earlier were released under MIT and stay MIT.
- README restructured to the House of Solance release layout.

### Unchanged
- The `query` command and `--json` keep every field they had. The map format on disk is the same.

## 1.2.0 — 2026-07-29

### Added
- `query --json` — machine-readable results (`query`, `hits`, `map_age_days`, `results[]` with path, title, score, bytes, modified, sections, snippet, links, backlinks). For scripting and for embedding vault-map in a larger local system.
- `search(terms, vault, top_n)` is now a public function that **returns** ranked results instead of printing them. `query()` is a thin printer over it, so an importing caller reuses the ranking rather than reimplementing it.

### Changed
- Nothing about the human output, the ranking weights, or the on-disk map format. `query` prints exactly what it printed in 1.1.0.

### Why
Compute and presentation were fused: the only way to reuse the ranking was to copy it or parse the human output. Both drift — a copy silently stops inheriting improvements, and the printed format is not an API. Splitting them is the fix.

## 1.1.0 — 2026-07-21

### Added
- `graph` command — writes a self-contained interactive `vault-map-graph.html` (canvas force-directed layout, pan/zoom, hover tooltips, click-to-highlight neighborhoods, node drag, folder legend with show/hide, search-and-jump). Zero network, zero dependencies; folder colors validated for colorblind safety on the dark surface.
- `path` command — shortest wikilink chain between two notes (BFS, name/title substring matching).

### Fixed
- Embedded JSON escapes `</` so a hostile note title cannot break out of the script block.

## 1.0.0 — 2026-07-21

First public release.

- `vault-map.py` — build a pure-local index of a markdown/Obsidian vault (titles, headings, wikilinks + backlinks, inline & frontmatter tags), then query it with ranked, snippeted, file-grade results. Zero dependencies, zero network, zero AI.
- Default vault: `$VAULT_MAP_DIR`, else the current directory.
- `MARKDOWN-GUIDE.md` — conventions for storing notes so retrieval stays cheap (the four recall signals + shape habits).
- MIT licensed. Independent implementation of the map-then-query idea pioneered by [Graphify](https://github.com/Graphify-Labs/graphify); no Graphify code used.
