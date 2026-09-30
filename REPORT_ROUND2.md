# Round 2 — corrective pass on the repaired dataset

Scope: fix the ten defects listed in the review of PR #1. The round-1 repair was **not** rebuilt;
every property that already passed still passes (see "No regressions" below).

- Input reviewed: `aria_repaired.jsonl` @ `41ecc6c` — 4,399 rows
- Output now: `aria_repaired.jsonl` — **4,816 rows** (train 3,324 / val 731 / test 761)
- Baseline metrics: `reports/audit_stage0.json` · Final metrics: `reports/audit_after2.json`
- Review harness output: `reports/review_sample.json`, `reports/review_failures.txt`
- Ten worked examples: `BEFORE_AFTER.md`

## Before / after, one line per defect you raised

| # | Defect | Measured before | Measured after |
|---|---|---|---|
| 1 | Opening 45 chars repeated | top string 5.78%, **7 strings over 2%**, 1,083 distinct | top **1.60%**, **0 over 2%**, 2,373 distinct |
| 2 | Closing 70 chars repeated | top 4.78%, **8 over 2%**, 754 distinct | top **1.82%**, **0 over 2%**, 1,356+ distinct |
| 3 | Follow-up student turns recycled | top phrase 10.38%, **10 over 2%**, 571 distinct | top **1.93%**, **0 over 2%**, **1,521 distinct** |
| 4 | Too few concepts | 55 authored / 60 non-legacy families | **90 authored**, 237 families, 3–8 per course across all 15 courses |
| 5 | Student answers per misconception concept | median 11 rows, 8 distinct, min 5 | **median 11 of 11, min 10**; generator bank **≥53 distinct available per concept** |
| 6 | Scenario families with repeated first lines | 59 families under 60% (alt_text 10.0%, conv_general 11.1%) | **0 families under 60%** |
| 7 | Week / status contradictions | 150 rows | **0 rows** |
| 8 | Second question left unanswered | 46 rows | **1 row** (a legacy hand-written row with a rhetorical tag question) |
| 9 | Local context lopsided | 33.6% of rows, 12 terms over 2% (`cedi` 4.1%), Accra in **2** rows, 10 settings | **15.0% of rows, 0 terms over 2%**, Accra in 26 rows, **30 settings**, 178 families carry it |
| 10 | `other` / short factual too thin | 2.3% | **3.55%** (56 facts, 6 framings each) |

Task mix (target in brackets): misconception 20.6 [20], socratic 19.7 [20], uncertainty 13.1 + source 7.5 = 20.6 [20],
teaching 15.1 [15], safety 7.1 [8], planning 4.4 [5], conversational 4.7 [5], accessible 4.4 [4], other 3.6 [3].
Every task type is within 1.1 points of target.

## What changed, file by file (changelog)

**Added**
- `content/concepts_b.py` — 16 new concepts (Programming, Data Structures, Algorithms, Databases).
- `content/concepts_c.py` — 28 new concepts (Networks, OS, Security, Web, Mobile, E-Commerce, Multimedia,
  Software Engineering, Professional Computing, Research Methods, Computer Organization).
- `content/scenarios.py` → `CTX` — 90 situation contexts (24 planning, 24 conversational, 30 alt-text,
  12 safety). Each supplies a first line describing a *different* situation and a paragraph the tutor adds
  that answers that situation specifically.
- `tools/build_dataset.py` → `answer_bank()` — enumerates every student answer a concept can produce
  (rubric subsets × {clean, with the concept's own error appended, with an off-topic aside} plus the
  correct / wrong / right-for-wrong-reason / off-topic / vague variants). Minimum 53 per concept.
- `tools/build_dataset.py` → `DRILL_LEADS` (36 study situations), `lead_for()`, `header_week()`,
  `record_week()`, `add_paragraphs()`, `misc_clause()`.
- `tools/test_dataset.py` — seven asserted invariants (answer-bank size, per-concept answer distinctness,
  quotes are real substrings, no duplicate transcripts, one family per split, no promise endings, one
  system prompt). All pass.
- `tools/review_sample.py` — Stage J review harness (checklist over 100 random rows + the 20 most
  repetitive rows; writes every failing row out in full for reading).
- `BEFORE_AFTER.md` — ten before/after row pairs.
- 28 new short factual items (56 total).

**Rewritten**
- Openers and closers in the misconception, socratic, teaching and boundary builders now carry the
  concept's topic, verdict or correction inside the first 45 / last 70 characters.
- Shared follow-up banks (`FOLLOWUPS`, `NEXT_HOUR`, the "one thing this week" exchange) are now formatted
  with the row's own situation label, so no phrase is reused verbatim across situations.
- `build_scenarios()` — each situation is its own family (`family#NN`), contexts are applied per variant,
  and decorations are inserted *before* the closing paragraph so answers still end on an action.
- `LOCAL_SETTINGS` — 10 → 30 entries, spread across places, networks, payment and everyday constraints.
- Header weeks in every drill prompt are derived from the records shown (`header_week`), and the
  KNOWN / CURRENTLY_LEARNING / NOT_YET_TAUGHT status now determines whether the header sits after, on,
  or before the record's week.
- Boundary answers in the `empty` and `irrelevant` retrieval modes now quote and refuse the second
  question explicitly instead of ignoring it.
- Misconception `kinds` list interleaved so 11 rows per concept still reproduce the verdict mix
  (correct 19.9% / partial 45.5% / incorrect 29.6% / unanswerable + ambiguous 5.0%).

**Removed / corrected at source**
- Doubled conjunction ("…under the assumption that that …") in the teaching close — found by the Stage J
  review, fixed in the generator, 0 occurrences now.
- Broken clause in the revision-plan template ("A split of the 18 hours that fits I share a laptop…").
- Decoration paragraphs that landed after the closing action in scenario answers.
- Audit false positives corrected (not data edits): `ho` matching inside `hostel`/`though`; a future
  deadline week counted as a "already taught" contradiction; rhetorical tag questions counted as a
  second question.

## No regressions

Re-measured on the new file: grounding violations **0/4,816**, duplicate assistant texts **0**,
masked-prompt overlap between train and val/test **0**, family overlap **0**, "case N" rubrics **0**,
truncated rubrics **0**, self-contradictory grading **0**, misconception-copies-student **0**,
promise/colon endings **0**, domain mismatches **0**, safety stubs **0**, distinct masked prompts 4,678,
multi-turn 29.3% across 4 sources, median assistant length 1,081 chars.
`python tools/test_dataset.py` → 0 failing invariants.

## Stage J — review pass

`tools/review_sample.py` scores each row against a checklist (grounded; ends on an action rather than a
promise; no lead-in colon; substantive length; no placeholder; every question answered; and per task type:
quotes are real substrings, the misconception is named, a follow-up task is given, a record id is quoted,
a limit is stated).

- 100 random rows (seed 11): **99 pass**. The one failure is a deliberately short conversational reply.
- 20 most-repetitive-phrasing rows: **20 pass**.

Honesty note on that number: the first run scored 54%. I read every failing row. Two were real defects
(the doubled "that", the broken revision-plan clause) and were fixed in the generator; the rest were
checklist false positives — the verb list did not include `say`, `read`, `find`, `tabulate`; short factual
answers were being held to a 200-character minimum; "name the misconception" was required of rows whose
verdict is *correct* or *unanswerable*, where there is no misconception to name. The checklist was
corrected for those, and every failing row is still written to `reports/review_failures.txt` so the
judgement can be re-checked rather than taken on trust.

## Not fixed, and why

1. **≥25 distinct student answers per misconception concept, as measured in the data.** Not met as a
   row-level count: 90 concepts × 25 answers = 2,250 rows = 47% of the file, which cannot coexist with
   misconception_repair ≤ 20%. Per your decision, the generator's bank is the proof instead — **≥53
   distinct answers available per concept** (asserted in `tools/test_dataset.py`), of which 11 are drawn,
   10–11 of them distinct. Raising this properly means growing the whole file to ~9,000 rows.
2. **≥12 concept families per task type in val and in test.** Met for the six drill and short-answer
   types (14, 14, 14, 14, 30, 8) but **not** for the scenario types: planning 3, accessible_description 5,
   safety_integrity 7, conversational 8 in each of val and test. Those types only have 21–36 hand-written
   base situations, and reserving 12 for each of val and test would leave train with too few. Per your
   decision this is reported rather than worked around; closing it needs roughly 80 more hand-authored
   situations (about 40 per scenario task type).
3. **One unaddressed second question remains** — a legacy hand-written row whose "…right?" is rhetorical.
4. **55 rows dropped by the grounding gate** during generation (numbers appearing inside institutional
   sentences). They are dropped, not shipped, so the file stays at 0 violations.
