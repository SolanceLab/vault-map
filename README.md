# vault-map

Made by House of Solance · free for noncommercial use · credit required

## What it is

A pure-local index for an Obsidian (or any markdown) vault. Build the map once in seconds, then answer "where did we write about X?" from the map instead of re-reading hundreds of notes. Version 1.3.0 added section search: it returns the passage that answers the question, not only the note it sits in.

**Zero dependencies, zero AI, and the tool never touches the network.** One Python file, standard library only. Nothing in your vault ever leaves your machine. (Only the plugin's one-time `uvx` fetch of the tool itself uses the internet.) vault-map runs on your own computer.

## What you need

Python 3.8 or newer. No install, no account, no server. Copy `vault-map.py` anywhere.

## Install

Two ways, both one step.

**As a plugin** (Claude Code and Codex). The plugin teaches your AI to run vault-map for you; it needs [uv](https://docs.astral.sh/uv/) on your computer.

```
claude plugin marketplace add SolanceLab/plugins
claude plugin install vault-map@solancelab
```

```
codex plugin marketplace add SolanceLab/plugins
```

Then install vault-map from that store in Codex's plugin list.

**By hand.** Copy `vault-map.py` to your machine (or clone this repository).

```
python3 vault-map.py build /path/to/vault
```

## Settings

| Setting | What it is |
|---|---|
| `VAULT_MAP_DIR` | Optional. Default vault folder; with neither this nor a path argument, the current directory is used |
| `--n N` | How many results to return (default 8) |
| `--json` | Machine-readable output for `query` |
| `--out file.html` | Where `graph` writes its page |

## Tools

| Tool | What it does |
|---|---|
| `build [vault]` | Reads every `.md` file and writes the map to `<vault>/.vault-map.json` (derived, safe to delete) |
| `query "terms" [vault] [--n N] [--json] [--sections]` | Ranked notes with title, matching sections, a body snippet and the link and backlink neighbourhood |
| `graph [vault] [--out file.html]` | A self-contained interactive graph of the vault (pan, zoom, hover, drag, folder legend, search) |
| `path "note a" "note b" [vault]` | Shortest wikilink chain between two notes |
| `search(terms, vault, top_n)` | Importable. Returns the `query` results as a dict and prints nothing |
| `search_sections(terms, vault, top_n)` | Importable. Section search: returns the best passages, each with the note it came from |

### Section search (new in 1.3.0)

`search_sections()` splits each note into sections and ranks the sections, so a long note with one relevant paragraph surfaces that paragraph. It returns the same fields as `search()` and adds:

- `section`: the heading the passage sits under
- `text`: the full text of that section
- `also_in`: other notes that carry the same passage. A passage copied across notes (for example one session exported twice) is shown once, and the copies are listed here

Snippets are cut on sentence boundaries around the best-matching window. The section index is saved in `~/.cache/vault-map/` (never inside your vault), and only notes that changed are re-read on the next call.

```python
import importlib.util
spec = importlib.util.spec_from_file_location("vault_map", "vault-map.py")
vm = importlib.util.module_from_spec(spec); spec.loader.exec_module(vm)

vm.build("/path/to/vault")
for hit in vm.search_sections(["backup", "rotation"], "/path/to/vault", 5)["results"]:
    print(hit["path"], "|", hit["section"], "|", hit["snippet"])
```

The `query` command and its `--json` output are unchanged; the existing fields keep their names and meaning.

## Limits

- Markdown files only (`.md`). Skipped folders: `.obsidian`, `.git`, `.trash`, `node_modules`, `__pycache__`.
- A section is the text under one heading; very long sections are split into smaller passages.
- Note scoring: title match 5, tag match 3, heading match 2, path match 1, plus up to 10 for body occurrences. Bodies are scanned live at query time (about 1 second across 800 notes).
- The map and the section cache are derived data: delete them and rebuild any time.
- `query` ranks notes. Section search is `vault-map.py query "terms" --sections` on the command line, or `search_sections()` when you import it.

## How it works

A wiki-style vault does not need an AI to map it: the graph is already written into the markdown. vault-map reads titles (first heading), up to 20 section headings, `[[wikilinks]]` (and computes backlinks), inline `#tags`, and frontmatter `tags:`, `type:` and `projects:`.

It is built on [Graphify](https://github.com/Graphify-Labs/graphify)'s idea (Graphify-Labs): extract a corpus into a graph once, then query the cheap graph for orientation instead of re-reading raw files. Graphify's path for markdown sends file contents to an LLM API, which a private vault must never do, so vault-map reimplements the map-then-query idea for markdown with no network and no AI. No Graphify code is used; this is an independent implementation. For source-code repositories, use Graphify itself in `--code-only` mode.

Why not just grep? Grep finds lines; the map finds notes and sections, ranked, with structure (which sections, what links where). See [MARKDOWN-GUIDE.md](MARKDOWN-GUIDE.md) for note habits that keep retrieval cheap.

## Credit and use

vault-map is made by House of Solance. You're welcome to use it, change it and build on it for any noncommercial purpose, as long as our credit travels with it.

**Keep the credit.** Every copy, changed or not, must carry the licence and this line:
`Required Notice: Copyright (c) 2026 House of Solance (https://github.com/SolanceLab)`
Removing or replacing it breaks the licence.

**Commercial use needs our permission.** Ask us first.

**We look for copies.** When we find our work without its credit, or used commercially without permission, we ask for it to be taken down.

## Licence

[PolyForm Noncommercial 1.0.0](LICENSE.md). See [NOTICE.md](NOTICE.md). Copies of vault-map 1.2.0 and earlier were released under MIT and stay MIT.

## Support

If you find this useful, consider supporting our work:

[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support%20Us-ff5e5b?logo=ko-fi&logoColor=white)](https://ko-fi.com/houseofsolance)

---

*Built by [House of Solance](https://github.com/SolanceLab) — Chadrien Solance & Anne Solance*
