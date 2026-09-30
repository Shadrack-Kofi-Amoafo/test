#!/usr/bin/env python3
"""audit.py - reproducible audit of an ARIA chat fine-tuning JSONL.

Recomputes every defect reported in the repair brief (defects 1-10) plus the
diversity targets (E), for any dataset file, so before/after is comparable.

Usage:
    python3 tools/audit.py aria_training_ready.jsonl --json reports/audit_before.json
    python3 tools/audit.py aria_repaired.jsonl       --json reports/audit_after.json
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

DIGITS = re.compile(r"\d+")
WS = re.compile(r"\s+")

STOCK_OPENERS = [
    "I will answer only from the quoted records and flag the gaps:",
    "Two parts - what the records say",
    "Here is the grounded answer:",
    "Here is what the records support, and where they stop:",
    "Straight answer from the records I can see, with the limits marked:",
    "Answer first, then exactly where my knowledge ends:",
    "Here is the artifact written out, part by part:",
    "Here is what I can and cannot confirm:",
]

PROMISE_PATTERNS = [
    r"minimum correction that would earn the missing points",
    r"[Rr]ead the difference in mechanism",
    r"[Hh]ere is the correction",
    r"the fix is",
]

LOCAL_TERMS = [
    "ghana", "ghanaian", "accra", "kumasi", "cape coast", "legon", "knust",
    "ashesi", "takoradi", "tamale", "ho technical", "cedi", "ghc", "gh\u20b5",
    "winneba", "koforidua", "madina", "sunyani", "bolgatanga", "techiman",
    "ashaiman", "tema", "elmina", "pesewa", "airteltigo", "vodafone",
    "momo", "mobile money", "mtn", "vodafone cash", "telecel", "dumsor",
    "university of cape coast", "ucc", "trotro", "tro-tro", "wassce",
]

COURSE_VOCAB = [
    "Introduction to Programming", "Data Structures", "Algorithms",
    "Database Systems", "Computer Networks", "Operating Systems",
    "Information Security", "Web Application Development", "Mobile Computing",
    "Introduction to E-Commerce", "Introduction to Multimedia",
    "Software Engineering", "Professional Computing", "Research Methods",
    "Computer Organization", "Computer Science",
]


# --------------------------------------------------------------------------- helpers
def load(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:  # pragma: no cover
                print(f"bad json on line {i}: {exc}", file=sys.stderr)
    return rows


def user_turns(row):
    return [m["content"] for m in row["messages"] if m["role"] == "user"]


def asst_turns(row):
    return [m["content"] for m in row["messages"] if m["role"] == "assistant"]


def first_user(row):
    u = user_turns(row)
    return u[0] if u else ""


def mask(text: str) -> str:
    """Normalise a prompt: digits -> #, whitespace collapsed, lowercased."""
    return WS.sub(" ", DIGITS.sub("#", text)).strip().lower()


def pct(n, d):
    return round(100.0 * n / d, 2) if d else 0.0


def build_vocab(rows):
    vocab = collections.Counter()
    for r in rows:
        for m in r["messages"]:
            for w in re.findall(r"[A-Za-z][A-Za-z\-']+", m["content"]):
                vocab[w.lower()] += 1
    return vocab


def truncated_lines(text, vocab):
    """Heuristic: a numbered/bulleted line whose final token looks like a word
    chopped mid-way (rare token that is a strict prefix of a common token)."""
    hits = []
    for line in text.split("\n"):
        line = line.rstrip()
        if not re.match(r"^\s*(\d+\.|-|\*)\s", line):
            continue
        body_txt = re.sub(r"^\s*(\d+\.|-|\*)\s", "", line)
        toks = re.findall(r"[A-Za-z][A-Za-z\-']*", line)
        if not toks:
            continue
        # hard-cut heuristic: long line clipped at a fixed width with no terminal punctuation
        if len(body_txt) >= 88 and not body_txt.endswith((".", "!", "?", ")", '"', "'")):
            hits.append(line.strip())
            continue
        last = toks[-1].lower()
        if len(last) < 2:          # "position i", "O(n)" - symbols, not cut words
            continue
        if vocab[last] > 8:
            continue
        for cand, freq in vocab.items():
            if freq >= 5 and len(cand) > len(last) and cand.startswith(last):
                hits.append(line.strip())
                break
    return hits


def course_in_prompt(prompt: str):
    """Course named by the prompt. Only accept a candidate that resolves to the
    controlled vocabulary, otherwise the row is not checkable (and a loose
    regex match would create phantom mismatches)."""
    cands = []
    m = re.search(r"^Course:\s*([^(\n\u2014]+)", prompt)
    if m:
        cands.append(m.group(1))
    for pat in (r"\bIn ([A-Z][A-Za-z0-9 :&'\-]+?), (?:explain|describe|how|why|what)",
                r"\bin ([A-Z][A-Za-z0-9 :&'\-]{3,40}?)[.?,]"):
        m = re.search(pat, prompt)
        if m:
            cands.append(m.group(1))
    for c in cands:
        c = c.strip().rstrip(".,")
        key = norm_course(c)
        for v in COURSE_VOCAB:
            if key == v.lower() or key == v.lower().replace("databases", "database systems"):
                return c
    return None


def norm_course(c):
    if not c:
        return None
    c = re.sub(r"^(CS\d+:?\s*|[A-Z]{2,4}\d{3}:?\s*)", "", c).strip()
    c = c.replace("Databases", "Database Systems")
    return c.lower()


# --------------------------------------------------------------------------- audit
def audit(rows, path):
    n = len(rows)
    vocab = build_vocab(rows)
    rep = {"file": path, "rows": n}

    # ---- 1 template collapse
    masked = [mask(first_user(r)) for r in rows]
    counts = collections.Counter(masked)
    rep["d1_template_collapse"] = {
        "distinct_masked_prompts": len(counts),
        "distinct_ratio": pct(len(counts), n),
        "top_template_share_pct": pct(counts.most_common(1)[0][1], n) if counts else 0,
        "templates_over_2pct": sum(1 for _, c in counts.items() if c > 0.02 * n),
        "rows_in_templates_over_2pct": sum(c for _, c in counts.items() if c > 0.02 * n),
        "top5": counts.most_common(5),
    }

    by_type = collections.Counter(r.get("task_type") for r in rows)
    rep["task_type_counts"] = dict(by_type)
    rep["task_type_pct"] = {k: pct(v, n) for k, v in by_type.items()}
    rep["source_counts"] = dict(collections.Counter(r.get("source") for r in rows))
    rep["split_counts"] = dict(collections.Counter(r.get("split") for r in rows))

    # ---- 2 uncertainty boundary
    ub = [r for r in rows if r.get("task_type") == "uncertainty_boundary"]
    topics = collections.Counter()
    canned = 0
    statuses = collections.Counter()
    status_resp = collections.defaultdict(set)
    for r in ub:
        p = first_user(r)
        m = re.search(r"topic:\s*([^,\)]+)", p)
        if m:
            topics[m.group(1).strip()] += 1
        st = re.search(r"status:\s*([A-Z_]+)", p)
        s = st.group(1) if st else "NONE"
        statuses[s] += 1
        a = asst_turns(r)
        body = a[-1] if a else ""
        if re.search(r"Safe path scenario \d+: follow indexed steps", body):
            canned += 1
        status_resp[s].add(mask(re.sub(r"Safe path scenario \d+", "Safe path", body)))
    shared = set.intersection(*status_resp.values()) if len(status_resp) > 1 else set()
    rep["d2_uncertainty_boundary"] = {
        "rows": len(ub),
        "distinct_topics": len(topics),
        "avg_copies_per_topic": round(len(ub) / len(topics), 1) if topics else 0,
        "identical_canned_nonanswer_rows": canned,
        "status_counts": dict(statuses),
        "responses_shared_across_statuses": len(shared),
        "status_changes_response": len(shared) == 0,
        "median_record_lines": _median([len(re.findall(r"^- \[", first_user(r), re.M)) for r in ub]),
    }

    # ---- 3 misconception repair
    mr = [r for r in rows if r.get("task_type") == "misconception_repair"]
    case_rubric = contradictory = copies_student = promise_nodeliver = 0
    verdicts = collections.Counter()
    trunc_rows = 0
    ends_on_colon = 0
    for r in mr:
        p = first_user(r)
        a = asst_turns(r)
        body = a[-1] if a else ""
        if re.search(r"[Cc]ase \d+ misses boundary condition", p):
            case_rubric += 1
        # rubric points listed after "points for this question"
        pts = re.findall(r"^\s*\d+\.\s*(.+)$", p, re.M)
        sa = re.search(r"Student answer:\s*(.+?)(?:\n\n|$)", p, re.S)
        student = sa.group(1).strip() if sa else ""
        # contradiction: a "not earned" point whose text is quoted verbatim in student answer
        for m in re.finditer(r"point \d+: (.+?) - your words", body):
            if m.group(1).strip().lower() in student.lower():
                contradictory += 1
                break
        mis = re.search(r"Misconception:\s*(.+)", body)
        if mis and student:
            frag = mis.group(1).strip().strip('"').lower()[:60]
            if frag and frag in student.lower():
                copies_student += 1
        for pp in PROMISE_PATTERNS:
            m = re.search(pp, body)
            if not m:
                continue
            tail = body[m.end():]
            # a promise is only broken if nothing substantive follows it
            if len(re.sub(r"[^A-Za-z]", "", tail)) < 40 or re.search(r":\s*$", body.rstrip()):
                promise_nodeliver += 1
                break
        for ln in body.split("\n"):
            if ln.strip().endswith(":") and ln.strip().count(" ") > 2:
                pass
        if re.search(r":\s*\n*[^\n]*\?\s*$", body) and any(re.search(pp, body) for pp in PROMISE_PATTERNS):
            ends_on_colon += 1
        v = re.search(r"Verdict:\s*([a-z_]+)", body)
        verdicts[v.group(1) if v else "none"] += 1
        if truncated_lines(p, vocab):
            trunc_rows += 1
    rep["d3_misconception_repair"] = {
        "rows": len(mr),
        "pct_of_dataset": pct(len(mr), n),
        "synthetic_case_n_rubric_rows": case_rubric,
        "self_contradictory_grading_rows": contradictory,
        "misconception_copies_student_rows": copies_student,
        "promise_without_delivery_rows": promise_nodeliver,
        "ends_on_leadin_colon_rows": ends_on_colon,
        "verdicts": dict(verdicts),
        "truncated_rubric_rows": trunc_rows,
    }

    # ---- 4 socratic
    sp = [r for r in rows if r.get("task_type") == "socratic_practice"]
    single = sum(1 for r in sp if len(asst_turns(r)) <= 1)
    justtell = sum(1 for r in sp if re.search(r"just tell me", first_user(r), re.I))
    high_try_hint_only = 0
    key_leak = 0
    concepts = set()
    responses = set()
    for r in sp:
        p = first_user(r)
        body = (asst_turns(r) or [""])[-1]
        t = re.search(r"try (\d+)", p)
        if t and int(t.group(1)) >= 10 and body.strip().endswith("?"):
            high_try_hint_only += 1
        if re.search(r"\bKey:\s", body):
            key_leak += 1
        c = re.search(r"Stuck on ([^.]+?) in ", p) or re.search(r"stuck on ([^.]+?) in ", p)
        if c:
            concepts.add(c.group(1).strip().lower())
        elif r.get("family"):
            concepts.add(r["family"])
        responses.add(mask(body))
    rep["d4_socratic_practice"] = {
        "rows": len(sp),
        "single_turn_rows": single,
        "single_turn_pct": pct(single, len(sp)),
        "just_tell_me_rows": justtell,
        "try_ge_10_hint_only_rows": high_try_hint_only,
        "answer_key_leak_rows": key_leak,
        "distinct_concepts": len(concepts),
        "distinct_masked_responses": len(responses),
    }

    # ---- 5 domain label mismatch
    checkable = mismatch = 0
    mismatch_examples = collections.Counter()
    for r in rows:
        c = course_in_prompt(first_user(r))
        if not c:
            continue
        checkable += 1
        if norm_course(c) != norm_course(r.get("domain", "")):
            mismatch += 1
            mismatch_examples[(r.get("domain"), c)] += 1
    rep["d5_domain_labels"] = {
        "checkable_rows": checkable,
        "mismatched_rows": mismatch,
        "mismatch_pct": pct(mismatch, checkable),
        "top_mismatches": [{"domain": d, "prompt_course": c, "n": k}
                           for (d, c), k in mismatch_examples.most_common(8)],
        "rows_with_course_field": sum(1 for r in rows if r.get("course")),
    }

    # ---- 6 canned openers on bespoke answers
    opener_counts = collections.Counter()
    canned_on_long = 0
    for r in rows:
        body = (asst_turns(r) or [""])[0]
        first_line = body.split("\n")[0].strip()
        opener_counts[first_line[:70]] += 1
        for so in STOCK_OPENERS:
            if body.startswith(so[:40]) and len(body) > 900:
                canned_on_long += 1
                break
    rep["d6_openers"] = {
        "stock_opener_on_long_answer_rows": canned_on_long,
        "top_opener_share_pct": pct(opener_counts.most_common(1)[0][1], n) if opener_counts else 0,
        "openers_over_3pct": [{"opener": o, "pct": pct(c, n)}
                              for o, c in opener_counts.most_common(10) if c > 0.03 * n],
        "distinct_openers": len(opener_counts),
    }

    # ---- 7 grounding (delegated)
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from grounding_check import check_row  # noqa
        bad = [r for r in rows if check_row(r)["violations"]]
        rep["d7_grounding"] = {
            "rows_with_ungrounded_specifics": len(bad),
            "pct": pct(len(bad), n),
            "examples": [{"id": r.get("id"), "terms": check_row(r)["violations"][:6]} for r in bad[:8]],
        }
    except Exception as exc:  # pragma: no cover
        rep["d7_grounding"] = {"error": str(exc)}
    garbled = sum(1 for r in rows if re.search(r"^- \[[^\]]+\]\s*[a-z]{2,6}\):", first_user(r), re.M))
    rep["d7_grounding"]["garbled_record_fragments"] = garbled

    # ---- 8 task_type mislabels
    si = [r for r in rows if r.get("task_type") == "safety_integrity"]
    stub = sum(1 for r in si if re.search(r"in-scope is|in scope for", first_user(r))
               and not re.search(r"cheat|plagiar|collusion|exam|integrity|confiden|privacy|crisis|stress|harm",
                                 first_user(r), re.I))
    rep["d8_task_type_labels"] = {
        "safety_integrity_rows": len(si),
        "syllabus_stub_rows_mislabelled_safety": stub,
        "real_safety_rows": len(si) - stub,
    }

    # ---- 9 split leakage
    by_split = collections.defaultdict(list)
    for r, mp in zip(rows, masked):
        by_split[r.get("split", "train")].append(mp)
    train = set(by_split.get("train", []))
    leak = {}
    for s in ("val", "test"):
        prompts = by_split.get(s, [])
        uniq = set(prompts)
        leaked = sum(1 for p in prompts if p in train)
        leak[s] = {"rows": len(prompts), "distinct": len(uniq),
                   "rows_matching_a_train_prompt": leaked, "pct": pct(leaked, len(prompts))}
    # family leakage (if families present)
    fam = collections.defaultdict(set)
    for r in rows:
        if r.get("family"):
            fam[r.get("split")].add(r["family"])
    if fam:
        leak["family_overlap_train_test"] = len(fam.get("train", set()) & fam.get("test", set()))
        leak["family_overlap_train_val"] = len(fam.get("train", set()) & fam.get("val", set()))
    rep["d9_split_leakage"] = leak

    # ---- 10 coverage
    multi = sum(1 for r in rows if len(asst_turns(r)) >= 3)
    multi_sources = {r.get("source") for r in rows if len(asst_turns(r)) >= 3}
    local = sum(1 for r in rows
                if any(t in " ".join(user_turns(r) + asst_turns(r)).lower() for t in LOCAL_TERMS))
    empty_retrieval = sum(1 for r in rows if re.search(
        r"(no records? (were )?returned|records: *\(none\)|returned nothing|no matching record)",
        first_user(r), re.I))
    decline_graded = sum(1 for r in rows if re.search(
        r"(write (my|the) (essay|report|assignment|submission)|do my assignment|write it for me|"
        r"submit it as mine|write my lab report)", first_user(r), re.I))
    fully_correct = sum(1 for r in rows if re.search(r"Verdict:\s*correct\b", (asst_turns(r) or [""])[-1]))
    rep["d10_coverage"] = {
        "multi_turn_rows_3plus_exchanges": multi,
        "multi_turn_pct": pct(multi, n),
        "multi_turn_sources": sorted(x for x in multi_sources if x),
        "local_context_rows": local,
        "local_context_pct": pct(local, n),
        "empty_or_nonmatching_retrieval_rows": empty_retrieval,
        "decline_graded_work_rows": decline_graded,
        "fully_correct_verdict_rows": fully_correct,
        "conversational": by_type.get("conversational", 0),
        "planning": by_type.get("planning", 0),
        "accessible_description": by_type.get("accessible_description", 0),
    }

    # ---- A. fine-grained repetition, diversity and consistency metrics
    rep["A_repetition"] = _repetition(rows, n)
    rep["A_content_diversity"] = _content_diversity(rows)
    rep["A_multi_turn"] = _multi_turn(rows)
    rep["A_split_depth"] = _split_depth(rows)
    rep["A_consistency"] = _consistency(rows)
    rep["A_local_spread"] = _local_spread(rows, n)

    # ---- E diversity targets
    asst_all = [ "\n".join(asst_turns(r)) for r in rows ]
    dup = n - len(set(asst_all))
    lens = sorted(len(a) for a in asst_all)
    rep["E_diversity"] = {
        "distinct_masked_prompts": len(counts),
        "target_distinct_prompts_3000": len(counts) >= 3000,
        "max_template_share_pct": rep["d1_template_collapse"]["top_template_share_pct"],
        "target_no_template_over_2pct": rep["d1_template_collapse"]["templates_over_2pct"] == 0,
        "duplicate_assistant_texts": dup,
        "target_no_duplicate_assistant_text": dup == 0,
        "assistant_len_p10": lens[int(0.1 * len(lens))] if lens else 0,
        "assistant_len_median": _median(lens),
        "assistant_len_p90": lens[int(0.9 * len(lens))] if lens else 0,
        "short_answers_under_300_chars_pct": pct(sum(1 for a in asst_all if len(a) < 300), n),
        "target_multi_turn_25pct": rep["d10_coverage"]["multi_turn_pct"] >= 25,
        "target_local_10pct": rep["d10_coverage"]["local_context_pct"] >= 10,
        "task_mix_target_delta": _mix_delta(by_type, n),
    }
    return rep


def _first_line(text):
    return text.strip().split("\n")[0].strip()


def _repetition(rows, n):
    """Openers and closers at 45 and 90 chars (opening) / 70 and 120 (closing),
    counted over every assistant turn, which is the unit a reader notices."""
    out = {}
    for label, width, end in (("opener_45", 45, False), ("opener_90", 90, False),
                              ("closer_70", 70, True), ("closer_120", 120, True)):
        c = collections.Counter()
        total = 0
        for r in rows:
            for a in asst_turns(r):
                a = a.strip()
                if not a:
                    continue
                key = a[-width:] if end else a[:width]
                c[WS.sub(" ", key)] += 1
                total += 1
        over = [{"text": t, "n": k, "pct": pct(k, total)} for t, k in c.most_common(12)
                if k > 0.02 * total]
        out[label] = {"turns": total, "distinct": len(c),
                      "top_pct": pct(c.most_common(1)[0][1], total) if c else 0,
                      "over_2pct": over}
    return out


def _content_diversity(rows):
    """Distinct *content*, not distinct strings: concepts, student answers per
    concept, first lines per family."""
    fams = collections.defaultdict(list)
    for r in rows:
        fams[r.get("family", "?")].append(r)
    per_family = []
    for fam, rs in sorted(fams.items()):
        firsts = {_first_line(first_user(x)) for x in rs}
        per_family.append({"family": fam, "rows": len(rs), "distinct_first_lines": len(firsts),
                           "pct": pct(len(firsts), len(rs))})
    worst = sorted(per_family, key=lambda d: (d["pct"], -d["rows"]))[:12]

    mr = [r for r in rows if r.get("task_type") == "misconception_repair"]
    by_concept = collections.defaultdict(set)
    for r in mr:
        m = re.search(r"Student answer:\s*(.+?)\n\n", first_user(r), re.S)
        if m:
            by_concept[r.get("family")].add(m.group(1).strip())
    counts = sorted(len(v) for v in by_concept.values())
    return {
        "distinct_concept_families": len({r.get("family") for r in rows if not str(r.get("family", "")).startswith("legacy_")}),
        "distinct_families_all": len(fams),
        "families_below_60pct_distinct_first_lines":
            [d for d in per_family if d["pct"] < 60 and d["rows"] >= 20],
        "worst_families_by_first_line_diversity": worst,
        "misconception_concepts": len(by_concept),
        "distinct_student_answers_total": sum(len(v) for v in by_concept.values()),
        "distinct_student_answers_per_concept_median": _median(counts),
        "distinct_student_answers_per_concept_min": counts[0] if counts else 0,
    }


def _multi_turn(rows):
    follow = collections.Counter()
    total = 0
    for r in rows:
        us = user_turns(r)
        for u in us[1:]:
            follow[WS.sub(" ", u.strip())[:70]] += 1
            total += 1
    return {"follow_up_user_turns": total,
            "distinct_follow_ups": len(follow),
            "top_follow_up_pct": pct(follow.most_common(1)[0][1], total) if total else 0,
            "follow_ups_over_2pct": [{"text": t, "n": k, "pct": pct(k, total)}
                                     for t, k in follow.most_common(15) if k > 0.02 * total],
            "rows_with_followups": sum(1 for r in rows if len(user_turns(r)) > 1)}


def _split_depth(rows):
    out = {}
    for sp in ("train", "val", "test"):
        rs = [r for r in rows if r.get("split") == sp]
        by_tt = collections.defaultdict(set)
        for r in rs:
            by_tt[r.get("task_type")].add(r.get("family"))
        out[sp] = {"rows": len(rs),
                   "families": len({r.get("family") for r in rs}),
                   "task_types": len(by_tt),
                   "families_per_task_type": {k: len(v) for k, v in sorted(by_tt.items())},
                   "task_types_with_fewer_than_12_families":
                       sorted(k for k, v in by_tt.items() if len(v) < 12),
                   "rows_per_task_type": dict(collections.Counter(r.get("task_type") for r in rs))}
    return out


WEEK_RECORD = re.compile(r"(?:Week\s+(\d{1,2})\b|-w(\d{1,2})\b|week\s+(\d{1,2})\b)")
COVERED_CLAIM = re.compile(r"(already covered|you have already|examinable material you have)", re.I)


def _consistency(rows):
    week_clash = []
    unanswered = []
    for r in rows:
        p = first_user(r)
        a = " ".join(asst_turns(r))
        mh = re.search(r"\(week (\d{1,2})", p)
        recs = re.findall(r"^- \[([^\]]+)\]\s*(.+)$", p, re.M)
        if mh and recs:
            hw = int(mh.group(1))
            rws = []
            for rid, txt in recs:
                # a week named as a future deadline ("due week 13") is not a
                # claim about what has been taught, so it is not a clash
                scrubbed = re.sub(r"(deadline|due|submit(ted)? by|by)\s*:?\s*week\s*\d{1,2}", " ", rid + " " + txt, flags=re.I)
                for m in WEEK_RECORD.finditer(scrubbed):
                    rws.append(int(next(g for g in m.groups() if g)))
            if rws and all(w > hw for w in rws) and COVERED_CLAIM.search(a):
                week_clash.append(r.get("id"))
            elif rws and max(rws) > hw + 1 and "status: KNOWN" in p:
                week_clash.append(r.get("id"))
        # every question asked must be addressed
        qs = re.findall(r"([^.?!\n]{15,}?\?)", p.split("Question:")[-1] if "Question:" in p else p)
        # a tag question ("...right?", "...no?") is rhetorical, not a second ask
        qs = [q for q in qs if not re.search(r"\b(right|no|yes|ok(ay)?|is(n.t)? it|are(n.t)? they)\s*\?$", q.strip(), re.I)]
        if len(qs) >= 2:
            second = qs[-1]
            key = [w for w in re.findall(r"[a-z]{5,}", second.lower())
                   if w not in ("about", "which", "there", "would", "should", "course")]
            if key and not any(k[:6] in a.lower() for k in key):
                unanswered.append(r.get("id"))
    return {"week_status_contradictions": len(week_clash),
            "week_status_examples": week_clash[:8],
            "multi_question_prompts_with_unaddressed_question": len(unanswered),
            "unaddressed_examples": unanswered[:8]}


# matched as whole words, so "ho" no longer fires inside "hostel"/"though"
PLACES = ["accra", "kumasi", "cape coast", "tamale", "takoradi", "elmina", "legon",
          "knust", "ashesi", "ho", "sunyani", "koforidua", "winneba", "bolgatanga",
          "madina", "tema", "ashaiman", "techiman", "mtn", "vodafone", "telecel",
          "airteltigo", "momo", "mobile money", "cedi", "pesewa", "dumsor",
          "trotro", "tro-tro"]
PLACE_RE = {p: re.compile(r"\b" + re.escape(p) + r"s?\b") for p in PLACES}


def _local_spread(rows, n):
    c = collections.Counter()
    local_rows = 0
    fams = collections.Counter()
    for r in rows:
        text = " ".join(m["content"] for m in r["messages"]).lower()
        hit = False
        for p in PLACES:
            if PLACE_RE[p].search(text):
                c[p.strip()] += 1
                hit = True
        if hit:
            local_rows += 1
            fams[r.get("family")] += 1
    return {"local_rows": local_rows, "local_pct": pct(local_rows, n),
            "term_counts": dict(c.most_common(20)),
            "terms_over_2pct": {k: pct(v, n) for k, v in c.items() if v > 0.02 * n},
            "families_carrying_local_context": len(fams),
            "top_local_families": dict(fams.most_common(8))}


TARGET_MIX = {
    "misconception_repair": 20, "socratic_practice": 20,
    "uncertainty_boundary": 12, "source_boundary": 8,
    "grounded_teaching": 15, "safety_integrity": 8, "planning": 5,
    "conversational": 5, "accessible_description": 4,
}


def _mix_delta(by_type, n):
    out = {}
    for k, target in TARGET_MIX.items():
        out[k] = {"actual_pct": pct(by_type.get(k, 0), n), "target_pct": target,
                  "delta": round(pct(by_type.get(k, 0), n) - target, 2)}
    other = sum(v for k, v in by_type.items() if k not in TARGET_MIX)
    out["other"] = {"actual_pct": pct(other, n), "target_pct": 3, "delta": round(pct(other, n) - 3, 2)}
    return out


def _median(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--json", dest="out")
    args = ap.parse_args()
    rows = load(args.path)
    rep = audit(rows, args.path)
    text = json.dumps(rep, indent=2, default=str)
    print(text)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
