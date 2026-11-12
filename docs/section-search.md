# vault-map section search

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
