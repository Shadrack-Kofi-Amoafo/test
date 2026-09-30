#!/usr/bin/env python3
"""Invariant tests for the repaired dataset and its generator.

Run:  python tools/test_dataset.py [dataset.jsonl]

These are the properties that must hold for the file to be usable for
fine-tuning. They are asserted rather than described, so a regression in the
generator fails loudly instead of quietly shipping.
"""
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_dataset import CONCEPTS, answer_bank          # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + name + (f"  [{detail}]" if detail else ""))
    if not ok:
        FAILS.append(name)


def main(path):
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]

    # 1. every concept can produce at least 25 distinct student answers
    banks = {c["key"]: {t for t, _, _ in answer_bank(c)} for c in CONCEPTS}
    smallest = min(banks.items(), key=lambda kv: len(kv[1]))
    check("answer bank >= 25 distinct answers for every concept",
          len(smallest[1]) >= 25, f"min {len(smallest[1])} ({smallest[0]})")

    # 2. the answers actually emitted for a concept are distinct from each other
    per = collections.defaultdict(list)
    for r in rows:
        if r["task_type"] != "misconception_repair":
            continue
        m = re.search(r"Student answer: (.+?)\n\nOfficial rubric", r["messages"][1]["content"], re.S)
        if m:
            per[r["family"]].append(m.group(1).strip())
    worst = min(((k, len(set(v)), len(v)) for k, v in per.items()), key=lambda x: x[1] / x[2])
    check("emitted student answers >= 90% distinct within every concept",
          worst[1] / worst[2] >= 0.9, f"worst {worst[0]} {worst[1]}/{worst[2]}")

    # 3. every quoted "you earned this" fragment is a real substring of the answer
    bad_quote = 0
    for r in rows:
        if r["task_type"] != "misconception_repair":
            continue
        prompt = r["messages"][1]["content"]
        m = re.search(r"Student answer: (.+?)\n\nOfficial rubric", prompt, re.S)
        if not m:
            continue
        ans = m.group(1).strip().lower()
        for q in re.findall(r'"([^"]{20,})"', r["messages"][2]["content"]):
            if q.strip().lower().rstrip(".") not in ans:
                bad_quote += 1
    check("graded quotes are real substrings of the student answer", bad_quote == 0, f"{bad_quote} bad")

    # 4. no two rows share an assistant transcript
    texts = ["\n".join(m["content"] for m in r["messages"] if m["role"] == "assistant") for r in rows]
    check("no duplicate assistant transcripts", len(set(texts)) == len(texts),
          f"{len(texts) - len(set(texts))} duplicates")

    # 5. a family lives in exactly one split
    fam_splits = collections.defaultdict(set)
    for r in rows:
        fam_splits[r["family"]].add(r["split"])
    leaked = [f for f, s in fam_splits.items() if len(s) > 1]
    check("every family lives in exactly one split", not leaked, f"{len(leaked)} leaked")

    # 6. no assistant turn ends on a promise or a lead-in colon
    tail_bad = 0
    for r in rows:
        last = [m["content"] for m in r["messages"] if m["role"] == "assistant"][-1].strip()
        if last.endswith(":") or re.search(r"(here is what I will do|I will explain( it)? below)\W*$", last, re.I):
            tail_bad += 1
    check("no answer ends on a promise or a lead-in colon", tail_bad == 0, f"{tail_bad} rows")

    # 7. the system prompt is the fixed ARIA prompt on every row
    sys_texts = {r["messages"][0]["content"] for r in rows}
    check("one fixed system prompt across the file", len(sys_texts) == 1, f"{len(sys_texts)} variants")

    print()
    print(f"{len(rows)} rows checked, {len(FAILS)} failing invariants")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ROOT / "aria_repaired.jsonl"))
