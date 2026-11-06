# vault-map contract

## Doors it offers

| Door | What it answers |
|---|---|
| `python3 vault-map.py build [vault]` | Builds the map of a markdown vault |
| `python3 vault-map.py query "terms" [vault] [--n N] [--json]` | Ranked notes, with snippets and link neighbourhood |
| `python3 vault-map.py graph [vault] [--out file.html]` | A self-contained interactive graph of the vault |
| `python3 vault-map.py path "a" "b" [vault]` | Shortest wikilink chain between two notes |
| `uvx --from git+https://github.com/SolanceLab/vault-map@v1.4.0 vault-map.py <command>` | The same commands, fetched and run by `uvx` (what the plugin's skill uses) |
| `search(terms, vault, top_n)` (import) | Ranked notes as a dict |
| `search_sections(terms, vault, top_n)` (import) | Ranked sections as a dict: the `search()` fields plus `section`, `text`, `also_in` |

## Data it owns

| Table / bucket / file | What is in it |
|---|---|
| `<vault>/.vault-map.json` | The note map (titles, headings, links, backlinks, tags). Derived, safe to delete |
| `~/.cache/vault-map/sections-*.pickle` | The saved section index, one per vault. Derived, safe to delete. Kept outside the vault |

## Settings and secrets it needs

Named here, never valued.

| Name | What it is |
|---|---|
| `VAULT_MAP_DIR` | Optional. The default vault folder (else the current directory) |

No keys, no network, no secrets.
