#!/usr/bin/env python3
"""Stage J review harness.

Pulls two samples - 100 random rows (seed 11) and the 20 rows whose opening
45 characters are the most repeated in the file - and scores each against a
fixed checklist. Rows that fail any item are written out in full so they can
be read rather than counted.

Run: python tools/review_sample.py [dataset.jsonl]
Writes reports/review_sample.json and reports/review_failures.txt
"""
import json
import random
import re
import sys
import collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.grounding_check import check_row                     # noqa: E402

PROMISE = re.compile(r"(here is what I will do|I will explain( it)? below|as follows:)\W*$", re.I)
TASK = re.compile(r"(\?|try |write |send me|give me|tell me|do only|start with|paste |draft |list |compute|"
                  r"measure|run |sketch|name |check |say |read |pick |predict|decide|apply |state |count |"
                  r"estimate|record |rewrite|reorganise|swap |explain |describe |keep that|do that|go and |time a|ask it|"
                  r"tabulate|capture|ping |plot |profile|simulate|instrument|find |add |mark it|spell)", re.I)


def checklist(r):
    """Returns {item: bool}. Every item is something a reader would object to."""
    prompt = r["messages"][1]["content"]
    asst = [m["content"] for m in r["messages"] if m["role"] == "assistant"]
    last = asst[-1].strip()
    all_a = "\n".join(asst)
    out = {}
    out["grounded"] = not check_row(r)["violations"]
    out["ends_on_action_not_promise"] = (r["task_type"] == "short_factual"
                                          or (bool(TASK.search(last[-400:])) and not PROMISE.search(last)))
    out["no_lead_in_colon_ending"] = not last.endswith(":")
    out["substantive_length"] = len(all_a) >= (60 if r["task_type"] == "short_factual" else 200)
    out["no_placeholder"] = not re.search(r"(case \d+|\[insert|TBD|lorem|xxx)", all_a, re.I)
    out["answers_every_question"] = True
    qs = [q for q in re.findall(r"([^.?!\n]{15,}?\?)", prompt.split("Question:")[-1])
          if not re.search(r"\b(right|no|ok(ay)?|is(n.t)? it)\s*\?$", q.strip(), re.I)]
    if len(qs) >= 2:
        key = [w for w in re.findall(r"[a-z]{5,}", qs[-1].lower())
               if w not in ("about", "which", "there", "would", "should", "course")]
        out["answers_every_question"] = (not key) or any(k[:6] in all_a.lower() for k in key)
    verdict = (r.get("verdict") or "")
    if r["task_type"] == "misconception_repair":
        m = re.search(r"Student answer: (.+?)\n\nOfficial rubric", prompt, re.S)
        ans = (m.group(1).strip().lower() if m else "")
        out["quotes_are_real"] = all(q.strip().lower().rstrip(".") in ans
                                     for q in re.findall(r'"([^"]{20,})"', all_a))
        # only meaningful where there is a wrong idea to name: an unanswerable
        # or fully correct answer has none
        out["names_misconception_in_own_words"] = verdict in ("correct", "unanswerable", "ambiguous") or bool(
            re.search(r"(what has gone wrong|what is actually going wrong|the misconception|the wrong idea|"
                      r"underneath this|the belief|what this assumes|the mistaken|the faulty assumption|"
                      r"the idea that needs replacing|named plainly|the assumption doing the damage|"
                      r"reading .{0,40} as)", all_a, re.I))
        out["gives_followup_task"] = bool(TASK.search(all_a[-700:]))
    if r["task_type"] in ("uncertainty_boundary", "source_boundary"):
        out["quotes_a_record_id"] = (r.get("retrieval_mode") == "empty"
                                     or bool(re.search(r"\[[a-z]+#", all_a)))
        out["states_a_limit"] = bool(re.search(r"(do(es)? not cover|not in my records|silent|cannot tell you|"
                                               r"no record|not something I can see|boundary)", all_a, re.I))
    return out


def main(path):
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    rng = random.Random(11)
    random_sample = rng.sample(rows, 100)

    openers = collections.Counter()
    for r in rows:
        for m in r["messages"]:
            if m["role"] == "assistant":
                openers[m["content"].strip()[:45]] += 1
    hot = {o for o, _ in openers.most_common(20)}
    repetitive = [r for r in rows
                  if any(m["role"] == "assistant" and m["content"].strip()[:45] in hot
                         for m in r["messages"])][:20]

    report, failures = {}, []
    for name, sample in (("random_100", random_sample), ("most_repetitive_20", repetitive)):
        item_fails = collections.Counter()
        passed = 0
        for r in sample:
            cl = checklist(r)
            if all(cl.values()):
                passed += 1
            else:
                for k, v in cl.items():
                    if not v:
                        item_fails[k] += 1
                failures.append((r["id"], r["task_type"], [k for k, v in cl.items() if not v],
                                 r["messages"][1]["content"][:600],
                                 "\n".join(m["content"] for m in r["messages"] if m["role"] == "assistant")[:1200]))
        report[name] = {"n": len(sample), "passed": passed,
                        "pass_rate_pct": round(100 * passed / max(1, len(sample)), 1),
                        "failures_by_item": dict(item_fails)}

    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "review_sample.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with open(ROOT / "reports" / "review_failures.txt", "w", encoding="utf-8") as fh:
        for rid, tt, items, p, a in failures:
            fh.write(f"===== {rid}  {tt}  failed: {', '.join(items)}\n--- PROMPT\n{p}\n--- ANSWER\n{a}\n\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ROOT / "aria_repaired.jsonl")
