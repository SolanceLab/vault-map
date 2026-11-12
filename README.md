# vault-map

Made by House of Solance · free for noncommercial use · credit required

vault-map finds where you wrote about something in your notes, in a second, without your AI reading them all.

<div align="center">

🗂️

*Your vault is a library you wrote yourself. Session notes, findings, half-finished ideas, years of it. Every note is a book, and the shelves never stop filling.*

*Now you need one passage: the day you decided something, the paragraph where you explained why. Without a map, your AI has to open the books one by one. It spends its tokens on pages that don't matter, and the passage you need is still on a shelf it never reached.*

**vault-map is the card catalogue.** *It reads every shelf once and writes a card for each book, each chapter, each paragraph. Ask where you wrote about something, and it opens the right drawer and points: this note, this section, these lines. Your AI goes straight there and reads only that.*

*The catalogue lives on your computer. It never writes in your books, and it never sends them anywhere.*

</div>

<p align="center"><img src="docs/how-it-works.svg" width="900" alt="Your AI asks vault-map once instead of reading every note. vault-map has read your vault once and keeps a catalogue on your computer: notes, their sections and their passages. It points to the one note, section and passage that answer, and your AI reads only that."></p>

## Quick start

**Let your AI do it.** Copy this and send it to Claude Code:

```
Please install vault-map for me. If uv is not installed, install it first:
claude plugin marketplace add SolanceLab/plugins
claude plugin install vault-map@solancelab
Then build the map of my vault and show me a search.
```

Using Codex? Send the same message with `codex plugin marketplace add SolanceLab/plugins`, then install vault-map from that store in Codex's plugin list.

**Or do it yourself:** run the two `claude plugin` lines from that message in your terminal (the plugin needs [uv](https://docs.astral.sh/uv/)).

**By hand.** Copy `vault-map.py` to your machine (or clone this repository).

```
python3 vault-map.py build /path/to/vault
```

## What it is

A pure-local index for an Obsidian (or any markdown) vault. Build the map once in seconds, then answer "where did we write about X?" from the map instead of re-reading hundreds of notes. Version 1.3.0 added section search: it returns the passage that answers the question, not only the note it sits in.

**Zero dependencies, zero AI, and the tool never touches the network.** One Python file, standard library only. Nothing in your vault ever leaves your machine. (Only the plugin's one-time `uvx` fetch of the tool itself uses the internet.) vault-map runs on your own computer.

## What you need

Python 3.8 or newer. No install, no account, no server. Copy `vault-map.py` anywhere.

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

Section search (`--sections`, `search_sections()`) returns the passage that answers, not the whole note; how it works and a Python example: [docs/section-search.md](docs/section-search.md).

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
