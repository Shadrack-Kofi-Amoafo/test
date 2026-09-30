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
