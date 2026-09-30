# ARIA dataset repair - audit, rebuild and verification

Everything below is recomputed by `tools/audit.py`, which runs on any JSONL in
this format. The "before" column is the shipped file `aria_training_ready.jsonl`
(3,617 rows); the "after" column is `aria_repaired.jsonl` (4,399 rows), built
deterministically by `tools/build_dataset.py`.

```bash
python3 tools/audit.py aria_training_ready.jsonl --json reports/audit_before.json
python3 tools/build_dataset.py                 # writes aria_repaired.jsonl + splits
python3 tools/audit.py aria_repaired.jsonl     --json reports/audit_after.json
python3 tools/grounding_check.py aria_repaired.jsonl
```

## A. The measured defects, verified then fixed

| # | Defect (as reported) | Measured before | After | How it was fixed |
|---|---|---|---|---|
| 1 | Template collapse | 861 distinct masked prompts / 3,617 rows | 3,709 / 4,399 | prompts are generated from a 47-concept bank with real content, varied framings and varied student answers; largest single template is 0.11% of rows |
| 2 | `uncertainty_boundary` non-answers | 855 rows of the identical "Safe path scenario N" stub; 33 topics; median 1 record line | 0 stub rows; 46 topics; median 2 record lines | records now carry real content (relevant / irrelevant / contradictory / stale / empty), the answer quotes the record id, states exactly what is not covered, and `status` changes the response |
| 3a | Synthetic "Case N misses boundary condition" rubric | 900 rows | 0 | real rubrics: 4 independent checkable points per concept, no case numbers |
| 3b | Self-contradictory grading | 900 rows | 0 | earned points are quoted from the student text, missing points are genuinely absent (both are constructed, not inferred) |
| 3c | "Misconception:" copies the student | 977 rows | 0 | the misconception is authored per concept and named in the tutor's words |
| 3d | Promise without delivery / ends on a colon | 174 / 81 rows | 0 / 0 | every graded answer ends with a concrete follow-up task; correction, mechanism and task are always present |
| 3e | Verdict mix | {"partially_correct": 991, "incorrect": 77, "correct": 2} | {"correct": 184, "partially_correct": 368, "incorrect": 276, "unanswerable": 29, "ambiguous": 17} | student answers span fully correct, partial, wrong-but-plausible, off-topic, right-for-the-wrong-reason and unmarkable |
| 3f | Truncated rubric strings | 93 rows | 0 | rubric and record text is authored whole; the builder rejects clipped lines |
| 4 | Socratic ladder | 91.81% single turn, 900 rows leaked "Key:", 68 hint-only rows at try>=10 | 28.96% single turn, 0 leaks, 0 hint-only at try>=10 | attempts 1-3 probe only, 4-7 targeted hint plus a smaller question, 8+ (or "just tell me" after real effort) a worked explanation followed by a transfer task |
| 5 | `domain` disagrees with the course in the prompt | 1583 of 2976 checkable rows (53.19%) | 0 of 2862 (0.0%) | `domain` is derived from a controlled course vocabulary, and a separate `course` field is present on every row |
| 6 | Canned opener on bespoke answers | 60 long answers began with a stock opener; top opener 3.98% | 0; top opener 3.41% | stock openers stripped from reused rows; generated answers open from their own content using rotating phrasing pools |
| 7 | Grounding violations / garbled records | 247 rows, 1 garbled fragment | 0, 0 | `tools/grounding_check.py` gates the build; rows that name an institutional specific absent from the prompt are rewritten or dropped |
| 8 | `safety_integrity` mislabels | 45 of 98 rows were syllabus stubs | 0 of 343 | stubs dropped; safety rows are authored integrity, welfare, privacy and over-reliance scenarios |
| 9 | Split leakage | val 128/168, test 140/183 prompts also in train | val 0/300, test 0/343; family overlap 0 | split by concept/template family globally, so a family is in exactly one split whatever task types it generates |
| 10 | Coverage gaps | multi-turn 3.37% from 1 source; local context 1.13%; 0 empty-retrieval, 0 decline-graded-work, 2 fully-correct rows | multi-turn 30.6% from 4 sources; local 21.03%; 92 empty/non-matching retrievals; 60 decline-the-deliverable rows; 184 fully-correct rows | new scenario families for graded-work refusal, exam integrity and collusion, bereavement and distress, confidentiality, shared credentials, AI over-reliance, and short factual questions |

## E. Diversity targets

| Target | Result | Met |
|---|---|---|
| >= 3,000 distinct prompts after digit masking | 3,709 | yes |
| No template above 2% of rows | max 0.11% | yes |
| No two rows with identical assistant text | 0 duplicates | yes |
| Multi-turn (3+ exchanges) >= 25%, >= 3 sources | 30.6% across legacy_authored, regen_agent, regen_scenario, regen_tutor | yes |
| >= 10% local (Ghanaian) context | 21.03% | yes |
| Task mix | {"misconception_repair": 19.87, "socratic_practice": 21.66, "uncertainty_boundary": 11.5, "source_boundary": 7.32, "grounded_teaching": 15.19, "safety_integrity": 7.8, "planning": 4.77, "conversational": 5.16, "accessible_description": 4.77, "short_factual": 1.95} | within ~1.7 points of every target |
| Length tracks need | p10 327 chars, median 1075, p90 1800; 9.34% of answers under 300 chars (short factual questions, simple in-scope lookups) | yes |

## C. Labels

* `course` - new field, controlled vocabulary of 15 course titles.
* `domain` - derived from the course named in the prompt, never from the seed generator.
* `task_type` - reconciled with content; a syllabus stub is no longer `safety_integrity`.
* `family` - concept or template family, the unit used for splitting.
* Extra per-type metadata: `verdict`, `earned_points`, `rubric_points`, `tier`, `attempt`, `retrieval_mode`, `status`, `evidence_lines`, `n_exchanges`.

## D. The grounding verifier

`tools/grounding_check.py` extracts every proper noun, form code, number and date
from each assistant turn and requires it to be (a) present in the user turns or
system prompt, (b) general knowledge of the subject (curated allowlist, e.g.
`bcrypt`, `443`, `64 bytes`), or (c) explicitly hedged ("the records do not name
a form"). Numbers are held to the strict standard whenever the sentence makes an
institutional claim - deadline, mark, fee, form, office, policy, date - which is
exactly the failure mode in the shipped data ("Compassionate Consideration",
"form CC-1", "Dean of Students" on a record that only said drastic decisions in
the first 48 hours are the worst ones). That row and 44 other legacy rows fail the
check and were dropped rather than kept with invented policy.

Self-test:

```
hallucinated policy -> CC-1, Compassionate Consideration, Dean, 14 March, 30
subject teaching    -> clean ("a cache line is typically 64 bytes")
grounded policy     -> clean (the date is quoted from the record)
```

## F. Re-split

Splits are assigned per *family* across the whole file, not per row: all rows
generated from one concept (`sec_password_storage`, `alt_text`, `safety_collusion`, ...)
land in the same split, whichever task type they belong to. Result: 3,756 train /
300 val / 343 test, with zero masked-prompt overlap and zero family overlap
between train and either evaluation split. Per-split files are written as
`aria_repaired_train.jsonl`, `aria_repaired_val.jsonl`, `aria_repaired_test.jsonl`.

## What was kept from the original file

310 hand-written rows (multi-turn Socratic teaching dialogues, authored
conversational and safety items, artefact descriptions) were reused after
stripping stock openers, re-deriving labels and passing the grounding gate.
Everything in the four drill task types was regenerated: those rows were
templated by construction and could not be repaired in place.

## Known limitations

* The concept bank is 47 concepts; the drill types therefore repeat concepts
  across rows even though prompts and answers differ. Adding concepts is the
  cheapest way to raise real diversity further - `content/concepts.py` is the
  only file to touch.
* Records are synthesised in the course's voice rather than extracted from a
  real course system; ids follow the original `source#slug` convention.
* The grounding verifier is a lexical gate. It catches invented policy, names,
  forms and figures; it cannot catch a plausible but wrong *explanation*, which
  is what the concept bank's authored content is for.
