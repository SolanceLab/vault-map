# Storing things in markdown so retrieval stays cheap

vault-map works on *any* markdown — unformatted notes are still found via full-body scan. But the map ranks and navigates using the structure your notes carry, so the more of these signals a note has, the faster and cheaper the right note surfaces. These habits also make your vault friendlier to grep, to Obsidian's own graph, and to any AI assistant reading it.

## The four recall signals

Give every note these four handles. Each one is something the map can grab that a wall of plain text doesn't offer.

**1. A descriptive first heading (H1).**
The first `#` heading becomes the note's title in search results, and title matches score highest. "Meeting notes" is invisible; "2026-07-14 — Deciding the backup rotation for the home NAS" is findable a year later by someone who only remembers "backup" or "NAS."

**2. Real section headings.**
Break the body with `##` headings that name what the section actually contains ("What broke", "The decision", "Follow-ups"). Headings are the map's mid-tier signal — and when a hit is shown, its section list often answers the question before the note is even opened.

**3. Frontmatter tags.**
A few consistent tags at the top:

```yaml
---
tags: [infra, backups, decision]
type: decision
---
```

Tags outrank body text in scoring because they're deliberate. Keep the vocabulary small and reused — five tags applied consistently beat fifty applied once. `type:` (note kind: decision, journal, howto, reference) and `projects:` fields are harvested too.

**4. Wikilinks — link liberally.**
`[[other-note]]` links build the connection graph: every query result shows what a note links to and what links back to it, which is often the real answer ("this decision connects to that incident"). A link to a note that doesn't exist yet is fine — it marks a thing worth writing. Notes with no links are islands; the map can find them but can't show you their neighborhood.

## Shape habits that compound

- **One topic per note.** A 200KB everything-dump matches every query weakly; ten focused notes each match their own query strongly. When a note grows past a few screens, split it and wikilink the parts.
- **Put dates in titles** for anything event-shaped (`2026-07-14 — ...`). Results are tie-broken by recency, but a date in the title survives file moves and exports.
- **Front-load the summary.** First paragraph = what this note is and what was concluded. Body snippets shown in results come from wherever the term first matches — a strong opening paragraph makes every snippet useful.
- **Name files like titles**, not `note(3).md`. The filename is the wikilink target and scores alongside the title.
- **Consistent vocabulary.** Pick one term per concept ("deploy", not deploy/ship/release/push-out interchangeably) — exact-match retrieval rewards the writer who repeats themselves.
- **Hub notes (Maps of Content).** For each big area, one note that's mostly wikilinks to the others. Hubs collect backlinks and become natural entry points.

## Anti-patterns

- **Untitled walls of text** — findable only by body scan, ranked weakly, snippet is your only clue.
- **Mega-transcripts with no headings** — one 600KB file can be *matched* but not *navigated*; add headings or split.
- **Tag soup** — dozens of unique-per-note tags carry no signal. Reuse or drop.
- **Structure in code blocks** — headings/links inside ``` fences are treated as text by most tools; keep real structure outside fences.

## Operational notes

- Rebuild after meaningful changes: `python3 vault-map.py build <vault>` — it's seconds; stale maps rank on old titles. Query output shows map age.
- `.vault-map.json` is derived data — safe to delete, gitignore it, never edit it.
- These conventions are exactly what mechanical exporters should emit too: if a script writes notes into your vault, make it emit the four signals (frontmatter tags, descriptive H1, real headings, wikilinks) so generated notes are as retrievable as hand-written ones.
