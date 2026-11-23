# CI fixtures

My real course PDFs can't go in a public repo, so CI runs against the sample notes in
[`samples/`](../../samples) instead. `questions.jsonl` has 22 questions written for
those notes: 19 answerable, each with its gold file and page, and 3 that the notes
don't cover so the answer eval can check the agent says so.

For Markdown, a "page" is a `#`/`##` section (a bare title is folded into the section
under it), so `{"file": "shortest-paths.md", "page": 4}` is the fourth section.

The full 50-question eval over the real material runs locally (`make eval`) and the
results get committed under `eval/results/<date>.json`.
