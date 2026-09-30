# ARIA dataset tooling

| File | What it does |
|---|---|
| `tools/audit.py` | Recomputes every defect metric and diversity target from a JSONL. `python3 tools/audit.py <file> --json <out>` |
| `tools/grounding_check.py` | Grounding verifier. Flags proper nouns, form codes, numbers and dates in assistant turns that are neither in the prompt/system message, nor subject general knowledge, nor hedged. |
| `tools/build_dataset.py` | Deterministic rebuild: writes `aria_repaired.jsonl` plus per-split files and `reports/build_report.json`. |
| `content/concepts.py` | 47 concept families: rubrics, misconceptions, corrections, mechanisms, probes, hints, worked explanations, transfer tasks, records (current and stale). Add concepts here to grow the set. |
| `content/scenarios.py` | Scenario families for safety/integrity, planning, conversational, accessible descriptions and short factual questions, plus Ghanaian study-condition settings. |

Reproduce everything:

```bash
python3 tools/audit.py aria_training_ready.jsonl --json reports/audit_before.json
python3 tools/build_dataset.py
python3 tools/audit.py aria_repaired.jsonl --json reports/audit_after.json
python3 tools/grounding_check.py aria_repaired.jsonl
```


## Round-2 additions

| Tool | What it does |
|---|---|
| `tools/test_dataset.py` | Asserted invariants: answer-bank size per concept, per-concept answer distinctness, quotes are real substrings, no duplicate transcripts, one family per split, no promise endings, one system prompt. Exit code 1 on any failure. |
| `tools/review_sample.py` | Stage J review harness. Scores 100 random rows (seed 11) and the 20 most repetitive rows against a per-task-type checklist; writes `reports/review_sample.json` and every failing row in full to `reports/review_failures.txt`. |
| `tools/audit.py` (extended) | Adds `A_repetition` (opener 45/90, closer 70/120 over every assistant turn), `A_content_diversity`, `A_multi_turn`, `A_split_depth`, `A_consistency`, `A_local_spread`. |

Concept banks are now split across `content/concepts.py` (46), `content/concepts_b.py` (16) and
`content/concepts_c.py` (28) — 90 in total; `tools/build_dataset.py` concatenates them.

Order to run everything:

```
python tools/build_dataset.py       # writes aria_repaired*.jsonl + reports/build_report.json
python tools/grounding_check.py aria_repaired.jsonl
python tools/audit.py aria_repaired.jsonl > reports/audit_after2.json
python tools/test_dataset.py
python tools/review_sample.py
```
