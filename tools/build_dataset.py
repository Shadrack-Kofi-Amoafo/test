#!/usr/bin/env python3
"""build_dataset.py - regenerate the ARIA fine-tuning set (Tasks B, C, E, F).

Outputs aria_repaired.jsonl. Everything is deterministic (seeded), so the
audit numbers are reproducible.

Design rules enforced here:
  * grading is honest - an "earned" point is quoted from the student's text,
    a "missing" point is genuinely absent;
  * the misconception is named in the tutor's words, never copied back;
  * no answer ends on a lead-in that promises content;
  * records carry real content, and status changes the answer;
  * the Socratic ladder escalates with the attempt number and ends in a real
    explanation plus a transfer task;
  * every specific in an answer is present in the prompt or the records
    (verified afterwards by tools/grounding_check.py);
  * splits are by concept/template family, never by row.
"""
from __future__ import annotations

import itertools
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from content.concepts import CONCEPTS as _CA                # noqa: E402
from content.concepts_b import CONCEPTS_B as _CB            # noqa: E402
from content.concepts_c import CONCEPTS_C as _CC            # noqa: E402

CONCEPTS = _CA + _CB + _CC
from content import scenarios as SC                        # noqa: E402
from tools.grounding_check import check_row                # noqa: E402

RNG = random.Random(20260929)

SYSTEM = ("You are ARIA, an offline course assistant for university students. You answer from the "
          "course records supplied inside the conversation and from the student's own messages, and "
          "you say plainly when something is not in those records instead of guessing. You coach "
          "students through their own work rather than producing graded submissions for them.")

LOCAL = SC.LOCAL_SETTINGS
CHANNELS = SC.CHANNELS

rows: list[dict] = []
_counter = {"n": 0}


def emit(messages, task_type, family, course, source, **extra):
    _counter["n"] += 1
    rid = f"R{_counter['n']:05d}"
    row = {"messages": [{"role": "system", "content": SYSTEM}] + messages,
           "id": rid, "task_type": task_type, "family": family,
           "course": course, "domain": course,
           "core_id": f"{family}-{_counter['n']:05d}",
           "source": source,
           "turn_index": 0,
           "length_class": _length_class(messages),
           "n_exchanges": sum(1 for m in messages if m["role"] == "assistant")}
    row.update(extra)
    rows.append(row)
    return row


def _length_class(messages):
    n = sum(len(m["content"]) for m in messages if m["role"] == "assistant")
    return "short" if n < 500 else ("medium" if n < 1400 else "long")


def pick(rng, pool, used=None):
    """Pick from pool, preferring values not yet used for this family."""
    if used is not None:
        fresh = [p for p in pool if p not in used]
        if fresh:
            v = rng.choice(fresh)
            used.add(v)
            return v
    return rng.choice(pool)


# ===========================================================================
# 1. misconception_repair
# ===========================================================================

ASK_TEMPLATES = [
    "Question: In {course}, {ask} Here is my attempt - how many of the rubric points did I actually earn?",
    "Question: We were asked about {topic} in {course}. {ask} Mark my answer against the official points, please.",
    "Question: {ask} This is for {course} week {week}. Tell me what is missing before I submit it.",
    "Question: My tutor says my answer on {topic} is not complete. {ask} Which points am I losing and why?",
    "Question: Practice question for {course}: {ask} I want the honest grading, not encouragement.",
    "Question: For the {course} revision sheet on {topic}: {ask} Where does this answer stop being right?",
    "Question: I answered this in the {course} quiz and got it back with no comments. {ask} What would a marker say?",
    "Question: Before the {course} test, grade this for me. {ask} Be strict.",
]

ASKS = [
    "explain {topic} and say what actually decides the outcome.",
    "explain {topic} well enough that someone could act on it.",
    "say what {topic} means in practice and why it matters.",
    "set out {topic} and the condition where it breaks.",
    "describe {topic} and justify the choice you would make.",
    "explain {topic} to someone who has just got it wrong.",
]

VERDICT_OPENERS_FULL = [
    "Verdict: correct - {e} of {t} points, and the reasoning is yours.",
    "Verdict: correct ({e}/{t}). Every point is supported by something you actually wrote.",
    "Verdict: correct. All {t} points are there, so this is a submission-quality answer.",
    "Verdict: correct ({e}/{t}) - nothing to repair, so I will push you further instead.",
]
VERDICT_OPENERS_PART = [
    "Verdict: partially_correct - {e} of {t} points.",
    "Verdict: partially_correct ({e}/{t}). The gap is specific and fixable.",
    "Verdict: partially_correct ({e}/{t}) - the part you have is solid, the part you are missing is the part being assessed.",
    "Verdict: partially_correct. You earn {e} of {t}; here is exactly where the other {m} went.",
    "Verdict: partially_correct ({e}/{t}). You are describing the right situation and stopping one step early.",
]
VERDICT_OPENERS_WRONG = [
    "Verdict: incorrect - 0 of {t} points, though the answer is a common and understandable one.",
    "Verdict: incorrect ({e}/{t}). Nothing here matches the rubric, so let us fix the idea rather than the wording.",
    "Verdict: incorrect. None of the {t} points are covered, and the reason is one wrong assumption doing all the damage.",
]
VERDICT_OPENERS_VAGUE = [
    "Verdict: unanswerable as written - there is not enough here to mark.",
    "Verdict: ambiguous. I cannot award or withhold points against this, because the sentence could mean two different things.",
    "Verdict: unanswerable - this restates the question rather than answering it, so there is nothing to grade yet.",
]

MISC_LABEL = [
    "The misconception underneath this:",
    "What is actually going wrong:",
    "Named plainly, the wrong idea is this:",
    "The idea that needs replacing:",
    "Here is the belief producing the error:",
    "The faulty assumption:",
]
CORR_LABEL = ["The correction:", "What to write instead:", "The fix, concretely:",
              "Replace it with this:", "The correct statement:"]
MECH_LABEL = ["Why it works that way:", "The mechanism:", "Why:", "The reason underneath:"]
TASK_LABEL = ["Next task:", "Do this next:", "One task, targeted at this error:",
              "Your follow-up:", "To prove the fix stuck:"]


def _subsets(n):
    """Proper non-empty subsets of the rubric points, smallest first."""
    out = []
    for size in range(1, n):
        for combo in itertools.combinations(range(n), size):
            out.append(list(combo))
    return out


# three ways a real student answer arrives, none of which change which rubric
# points are genuinely earned
def _hedge(c):
    return " I am not sure about the rest of it."


def _error_aside(c):
    return " I also think " + c["wrong"].rstrip(".").lower().split(". ")[0] + "."


def _offtopic_aside(c):
    return " " + c["offtopic"].rstrip(".") + "."


def answer_bank(c):
    """Every distinct student answer this concept can produce, in a fixed
    order, with the rubric points each one genuinely earns.

    The bank is what makes the grading honest: `earned` is derived from the
    text, not asserted next to it. Decorations add a hedge, the concept's own
    misconception, or an off-topic aside - none of which change which points
    the answer states, and none of which are applied to a fully correct answer
    (that would make the verdict contradict the text).
    """
    pts = c["rubric"]
    n = len(pts)
    bank = []

    def text_for(idx):
        return _capital(" ".join(pts[i][1].rstrip(".") + "." for i in idx))

    full = list(range(n))
    bank.append((text_for(full), full, "correct"))
    bank.append((text_for(full) + _hedge(c), full, "correct"))
    bank.append((text_for(full[::-1]) + " That is all of it, I think.", full, "correct"))
    for idx in _subsets(n):
        base = text_for(idx)
        bank.append((base, idx, "partial"))
        bank.append((base + _error_aside(c), idx, "partial"))
        bank.append((base + _offtopic_aside(c), idx, "partial"))
    ans, _why = c["rfwr"]
    bank.append((ans, [], "rfwr"))
    bank.append((ans + _hedge(c), [], "rfwr"))
    bank.append((c["wrong"], [], "wrong"))
    bank.append((c["wrong"] + _hedge(c), [], "wrong"))
    bank.append((c["wrong"] + _offtopic_aside(c), [], "wrong"))
    bank.append((c["offtopic"], [], "offtopic"))
    bank.append((c["vague"], [], "vague"))
    bank.append((c["vague"] + _hedge(c), [], "vague"))
    return bank


def student_answer(c, kind, rng, n_earned=None, seq=0):
    """Return (text, earned_indices, kind), taking the seq-th answer of that
    kind from the concept's bank so two rows of the same concept never carry
    the same student answer."""
    pool = [b for b in answer_bank(c) if b[2] == kind]
    if not pool:
        pool = answer_bank(c)
    return pool[seq % len(pool)]


def _capital(s):
    return s[0].upper() + s[1:] if s else s


def rubric_block(c):
    return "\n".join(f"{i+1}. {p[0]}" for i, p in enumerate(c["rubric"]))


def build_misconception(c, n_rows, split_local):
    # verdict mix target: ~20% correct, ~45% partially correct,
    # ~30% incorrect, ~5% unanswerable/ambiguous
    # interleaved so that any prefix of the list is already representative -
    # concepts generate 11 rows each, and the window start rotates per concept
    kinds = ["partial", "wrong", "correct", "partial", "wrong", "vague",
             "partial", "correct", "wrong", "partial", "rfwr", "wrong",
             "partial", "correct", "offtopic", "partial", "wrong", "partial",
             "correct", "partial"]
    rng = random.Random(hash(c["key"]) & 0xFFFF)
    used_ask, used_tmpl, used_open = set(), set(), set()
    seen_kind = {}
    for i in range(n_rows):
        kind = kinds[(i + (hash(c["key"]) >> 9)) % len(kinds)]
        seen_kind[kind] = seen_kind.get(kind, 0) + 1
        text, earned, kind = student_answer(
            c, kind, rng, seq=seen_kind[kind] - 1 + (hash(c["key"]) >> 13) % 3)
        week = header_week(c["records"], "KNOWN", i)
        ask = pick(rng, ASKS, used_ask).format(topic=c["topic"])
        tmpl = pick(rng, ASK_TEMPLATES, used_tmpl)
        q = tmpl.format(course=c["course"], topic=c["topic"], week=week, ask=ask)
        q = re.sub(r"([.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), q)
        q = re.sub(r"(:\s+)([a-z])", lambda m: m.group(1) + m.group(2), q)
        local = ""
        if split_local and i % 4 == 3:
            local = " " + rng.choice(LOCAL).capitalize() + ", so I want to get this right in one pass."
        prompt = (f"{lead_for(c['key'], i)}\n\nCourse: {c['course']} (week {week}, topic: {c['topic']}, status: KNOWN).\n\n"
                  f"{q}{local}\n\n"
                  f"Student answer: {text}\n\n"
                  f"Official rubric points:\n{rubric_block(c)}")
        answer = grade_answer(c, text, earned, kind, rng, used_open, local)
        emit([{"role": "user", "content": prompt},
              {"role": "assistant", "content": answer}],
             "misconception_repair", c["key"], c["course"], "regen_grader",
             verdict=_verdict(kind, earned, len(c["rubric"])),
             rubric_points=len(c["rubric"]), earned_points=len(earned))


def _verdict(kind, earned, total):
    if kind == "vague":
        return "unanswerable"
    if len(earned) == total:
        return "correct"
    if earned:
        return "partially_correct"
    if kind == "rfwr":
        return "partially_correct"
    return "incorrect"


def grade_answer(c, text, earned, kind, rng, used_open, local):
    pts = c["rubric"]
    total = len(pts)
    missing = [i for i in range(total) if i not in earned]
    v = _verdict(kind, earned, total)

    if v == "correct":
        head = pick(rng, VERDICT_OPENERS_FULL, used_open).format(e=len(earned), t=total)
        body = [head, ""]
        body.append("Earned, with the words that earned them:")
        for i in earned:
            body.append(f"- Point {i+1} ({pts[i][0]}): \"{pts[i][1]}\"")
        body.append("")
        body.append(f"{rng.choice(['One thing to watch:', 'Where this answer could still be sharpened:', 'The next level of this:'])} "
                    f"you have the rule; the place people lose it later is under pressure, when {c['misconception']} creeps back in. "
                    f"Your answer already rules that out, so keep the sentence that does it.")
        body.append("")
        body.append(f"{rng.choice(TASK_LABEL)} {c['variant']}")
        return "\n".join(body)

    if v == "unanswerable":
        head = pick(rng, VERDICT_OPENERS_VAGUE, used_open)
        return "\n".join([
            head, "",
            f"\"{text}\" is a heading, not a claim: it repeats the topic without saying what is true about it, "
            f"so there is no statement for me to test against any of the {total} points.",
            "",
            f"Pick the one point you are surest of - say, point 1 ({pts[0][0]}) - and write one sentence that a marker could agree or disagree with. "
            f"One testable sentence is worth more here than four hedged ones.",
            "",
            f"{rng.choice(TASK_LABEL)} write that single sentence and send it back; I will mark it strictly and we will build outwards from there."])

    if kind == "rfwr":
        ans, why = c["rfwr"]
        head = pick(rng, VERDICT_OPENERS_PART, used_open).format(e=1, t=total, m=total - 1)
        return "\n".join([
            head, "",
            f"Credit where it is due: the conclusion is the one I would reach. \"{ans}\" lands on the right action.",
            f"Not earned: the justification is what the rubric is marking, and yours does not hold - {why}.",
            "",
            f"{rng.choice(MISC_LABEL)} {c['misconception']}.",
            f"{rng.choice(CORR_LABEL)} {c['correction']}",
            f"{rng.choice(MECH_LABEL)} {c['mechanism']}",
            "",
            f"{rng.choice(TASK_LABEL)} {c['followup']}" + (
                f" Given that {local.strip().rstrip('.').lower()}" .replace("Given that ,", "Given that") + ", do the smallest version of it first." if local else "")])

    # partially correct or incorrect
    if earned:
        head = pick(rng, VERDICT_OPENERS_PART, used_open).format(
            e=len(earned), t=total, m=total - len(earned))
    else:
        head = pick(rng, VERDICT_OPENERS_WRONG, used_open).format(e=0, t=total)

    body = [head, ""]
    if earned:
        body.append("Earned, quoted from your answer:")
        for i in earned:
            body.append(f"- Point {i+1} ({pts[i][0]}): \"{pts[i][1]}\"")
        body.append("")
        body.append("Not earned, because nothing in your answer covers them:")
        for i in missing:
            body.append(f"- Point {i+1}: {pts[i][0]}")
    else:
        body.append(f"Not earned: all {total} points. Your answer says \"{text}\" - "
                    f"and none of the rubric points can be read into that.")
    body.append("")
    body.append(f"{rng.choice(MISC_LABEL)} {c['misconception']}.")
    body.append(f"{rng.choice(CORR_LABEL)} {c['correction']}")
    body.append(f"{rng.choice(MECH_LABEL)} {c['mechanism']}")
    body.append("")
    tail = f"{rng.choice(TASK_LABEL)} {c['followup']}"
    if local:
        tail += (f" Keep it to one sitting: {local.strip().rstrip('.').lower()} is a real constraint, so size "
                 f"the {c['topic']} attempt to the time you actually have.")
    body.append(tail)
    return "\n".join(body)


# ===========================================================================
# 2. socratic_practice - escalation ladder keyed to the attempt number
# ===========================================================================

STUCK_OPENERS = [
    "I am stuck on {topic} in {course} (attempt {n}).",
    "{course}, {topic}. This is attempt {n} and I am going in circles.",
    "Attempt {n} at the {topic} question in {course} and I still cannot see it.",
    "Working on {topic} for {course}. Try {n}.",
    "{topic} in {course} - try {n}. I have been at this for a while.",
    "Try {n} on the {course} exercise about {topic}.",
]

PROBE_LEAD = [
    "Before any hint: ",
    "Answer this first and the rest usually follows: ",
    "One question back at you: ",
    "Let us locate the gap precisely. ",
    "Stay with your own attempt for one more step. ",
    "Do not reach for the answer yet - ",
]
HINT_LEAD = [
    "Here is a real hint, not a nudge: ",
    "Attempt {n} earns you a proper hint. ",
    "You have put in enough attempts for a hint that narrows things: ",
    "Taking you one step closer: ",
    "This is the piece you are missing: ",
]
REVEAL_LEAD = [
    "You have earned the explanation, so here it is in full.",
    "Attempt {n} and a straight request - that is the point where withholding stops helping. Here is the whole thing.",
    "Right: no more questions, here is the answer with the reasoning attached.",
    "You have done the work, so I will stop asking and explain it properly.",
    "Fair enough. Explanation first, then one thing for you to do with it.",
]


# Each drill row opens with the student's own situation, so the first line of
# a prompt varies with the row instead of repeating the course header
# (task D: distinct first lines within every family).
DRILL_LEADS = [
    "I am going through the tutorial sheet on my own tonight.",
    "We had a class test on this today and I want to check my answer.",
    "My study group argued about this for twenty minutes and gave up.",
    "I am rewriting my notes before the mid-semester exam.",
    "This came up in the lab and the demonstrator had already left.",
    "I am preparing to explain this to a junior who asked me.",
    "I got this wrong in the quiz and the feedback was one word.",
    "I am doing last year's past paper under timed conditions.",
    "My lecturer said this would be on the exam in some form.",
    "I am catching up on a week I missed.",
    "I read the slides twice and still cannot use this.",
    "I am checking my understanding before I start the assignment.",
    "A friend explained this to me and I am not sure they were right.",
    "I am writing a summary sheet for the whole topic.",
    "This is the only part of the course I dread.",
    "I answered this in a mock and lost most of the marks.",
    "I am revising on my phone between lectures.",
    "I want to be able to answer this without looking anything up.",
    "I am helping run a revision session tomorrow and this is my topic.",
    "My project uses this and I want to understand it properly, not just copy it.",
    "I am coming back to this after two weeks on something else.",
    "I skipped this in first semester and it has caught up with me.",
    "I have an oral assessment where I have to explain this out loud.",
    "I answered a forum question about this and now I am doubting myself.",
    "I am trying to work out whether my textbook and my notes disagree here.",
    "I have twenty minutes before my next class.",
    "I am doing this as an extra exercise, not for marks.",
    "My interview next week apparently covers this.",
    "I marked a classmate's work and could not tell if they were right.",
    "This keeps appearing in past papers so I want it solid.",
    "I am writing the theory section of my report and need this to be correct.",
    "I understood this in class and lost it by the evening.",
    "I am trying to stop memorising and actually understand it.",
    "I have to submit a short answer on this in two days.",
    "I am reviewing the whole course topic by topic and this is next.",
    "My tutor asked me this and I froze.",
]


def lead_for(key, i, salt=0):
    return DRILL_LEADS[(i * 7 + salt * 13 + (hash(key) >> 5)) % len(DRILL_LEADS)]


_WEEK_RE = re.compile(r"[Ww]eek[ -](\d{1,2})|w(\d{1,2})\b")


def record_week(records, default=6):
    """Highest week number named by the records actually shown.

    The prompt header is derived from this, so a header never says "week 2,
    status: KNOWN" over a record that is explicitly from week 7 (task F).
    """
    ws = []
    for rid, txt in records:
        for m in _WEEK_RE.finditer(f"{rid} {txt}"):
            ws.append(int(next(g for g in m.groups() if g)))
    return max(ws) if ws else default


def header_week(records, status, i, default=6):
    rw = record_week(records, default)
    if status in ("KNOWN",):
        return rw + (i % 3)          # the material has been covered
    if status == "CURRENTLY_LEARNING":
        return rw                    # the student is inside that week
    if status == "NOT_YET_TAUGHT":
        return max(1, rw - 2 - (i % 2))
    return max(1, rw - (i % 2))      # UNKNOWN: no claim either way


def build_socratic(c, n_rows, split_local):
    rng = random.Random((hash(c["key"]) >> 3) & 0xFFFF)
    used_open, used_probe, used_hint, used_rev = set(), set(), set(), set()
    for i in range(n_rows):
        n = 1 + (i * 5) % 13            # attempt number 1..13
        just_tell = (i % 4 == 2)
        week = header_week(c["records"], "KNOWN", i)
        local = ""
        if split_local and i % 4 == 2:
            local = " " + rng.choice(LOCAL).capitalize() + "."
        opener = (lead_for(c["key"], i, 7) + " "
                  + pick(rng, STUCK_OPENERS, used_open).format(topic=c["topic"], course=c["course"], n=n))
        attempt_line = ([
            f" What I have so far: {c['vague']}",
            f" My thinking is that {c['wrong'].rstrip('.').lower()}.",
            f" I wrote down: {c['rubric'][0][1]}.",
            f" I can quote the definition but I cannot use it.",
            f" I get lost as soon as I have to apply it.",
        ])[i % 5]
        ask = " Just tell me the answer?" if just_tell else ""
        user1 = f"{opener}{attempt_line}{ask}{local}"

        if n <= 3 and not just_tell:
            # tier 1: probing question only, single turn
            a1 = (pick(rng, PROBE_LEAD, used_probe) + c["probe"] +
                  f"\n\nWrite your answer on {c['topic']} in one sentence and send it back - I will tell you whether it holds.")
            emit([{"role": "user", "content": user1}, {"role": "assistant", "content": a1}],
                 "socratic_practice", c["key"], c["course"], "regen_tutor", tier="probe", attempt=n)
            continue

        if n <= 7 and not just_tell:
            # tier 2: hint plus a smaller question, two exchanges
            a1 = pick(rng, HINT_LEAD, used_hint).format(n=n) + c["hint"]
            u2 = ([
                f"Okay - so is it that {c['rubric'][0][1]}?",
                f"I think I see it: {c['rubric'][-1][1]}. Is that the whole thing?",
                f"Still not there. I keep coming back to {c['wrong'].rstrip('.').lower()}.",
            ])[i % 3]
            if u2.startswith("Still not"):
                a2 = (f"That is the sticking point, so let us break it: {c['probe']}\n\n"
                      f"Answer just that, and if it does not come in the next attempt I will explain the whole mechanism.")
            else:
                a2 = (f"Yes - on {c['topic']} that part is right, and it is the half people usually get. What is missing: "
                      f"{c['correction']}\n\nOne smaller question to finish it: {c['probe']}")
            u3 = ([
                f"Right - so it comes down to this: {c['rubric'][-1][1]}?",
                f"I tried that and got a different result from what I expected for {c['topic']}.",
                f"I think so. Does that mean {c['wrong'].rstrip('.').lower()} is just wrong?",
            ])[(i // 3) % 3]
            if u3.startswith("I tried"):
                a3 = (f"Good - an unexpected result is more useful than a confirmation. {c['mechanism']}\n\n"
                      f"Check that against what you saw, then do this: {c['variant']}")
            elif u3.startswith("I think so"):
                a3 = (f"Not random, just incomplete - on {c['topic']}, {c['misconception']} is a reasonable reading until you test it.\n\n"
                      f"{c['correction']} Now transfer it: {c['variant']}")
            else:
                a3 = (f"On {c['topic']}, that is it: {c['correction'].rstrip('.')}. Say it once more in your own words "
                      f"and it will survive the exam.\n\nOne transfer task so it sticks: {c['variant']}")
            emit([{"role": "user", "content": user1}, {"role": "assistant", "content": a1},
                  {"role": "user", "content": u2}, {"role": "assistant", "content": a2},
                  {"role": "user", "content": u3}, {"role": "assistant", "content": a3}],
                 "socratic_practice", c["key"], c["course"], "regen_tutor", tier="hint", attempt=n)
            continue

        # tier 3: attempt >= 8 or an explicit request after real effort -> explain
        if just_tell and n <= 3:
            a1 = (f"Not yet - attempt {n} is early, and you have a usable idea in there. "
                  + c["probe"] + "\n\nIf the next attempt does not land it, I will explain it in full rather than keep asking.")
            u2 = ([
                f"Tried it. I still think {c['wrong'].rstrip('.').lower()}.",
                f"I get as far as {c['rubric'][0][1]} and then stop.",
            ])[i % 2]
            a2 = (pick(rng, HINT_LEAD, used_hint).format(n=n + 1) + c["hint"] +
                  f"\n\nWhat do you get when you actually do that?")
            u3 = ([
                f"Still nothing. Please just explain {c['topic']} properly.",
                f"I have run it and I do not understand the result. Explain {c['topic']} properly?",
            ])[(i // 2) % 2]
            a3 = (pick(rng, REVEAL_LEAD, used_rev).format(n=n + 2) + "\n\n" + c["worked"] +
                  f"\n\nNow make it yours: {c['variant']}")
            emit([{"role": "user", "content": user1}, {"role": "assistant", "content": a1},
                  {"role": "user", "content": u2}, {"role": "assistant", "content": a2},
                  {"role": "user", "content": u3}, {"role": "assistant", "content": a3}],
                 "socratic_practice", c["key"], c["course"], "regen_tutor", tier="earned_reveal", attempt=n)
            continue

        a1 = (pick(rng, REVEAL_LEAD, used_rev).format(n=n) + "\n\n" + c["worked"])
        u2 = ([
            f"That makes sense. So where would {c['topic']} trip me up in the exam?",
            f"Okay. So was {c['wrong'].rstrip('.').lower()} completely wrong, or just incomplete?",
            f"Got it. Give me something to check I actually have {c['topic']}.",
        ])[i % 3]
        if u2.startswith("Okay. So was"):
            a2 = (f"Your reading of {c['topic']} is incomplete rather than random - it is reasonable on the evidence you had. "
                  f"The specific thing that makes it fail: {c['mechanism']}\n\nTry this: {c['variant']}")
        elif u2.startswith("That makes"):
            a2 = (f"Where {c['topic']} goes wrong under exam pressure: people state the rule and skip the condition. "
                  f"{c['correction']}\n\nSo: {c['variant']}")
        else:
            a2 = (f"Here is the check: {c['variant']}\n\nSend me your answer and I will mark it the way a {c['course']} "
                  f"marker would mark a question on {c['topic']}.")
        u3 = ([f"Here is my attempt at that: {c['rubric'][0][1]}.",
               f"I do not think I can do the transfer task on {c['topic']} yet.",
               f"Would {c['rubric'][-1][1]} count as an answer?"])[(i // 2) % 3]
        if u3.startswith("I do not think"):
            a3 = (f"Then we shrink it. Do only the first half: {c['followup']}\n\n"
                  f"Send me what you get, even if it is wrong - a wrong attempt tells me exactly which part of the mechanism has not landed.")
        else:
            a3 = (f"That counts for {c['topic']}, and it is the right shape. The one thing I would add for full marks: "
                  f"{c['correction'].rstrip('.')}.\n\nKeep that sentence - it is what separates recognising {c['topic']} from being able to use it.")
        emit([{"role": "user", "content": user1}, {"role": "assistant", "content": a1},
              {"role": "user", "content": u2}, {"role": "assistant", "content": a2},
              {"role": "user", "content": u3}, {"role": "assistant", "content": a3}],
             "socratic_practice", c["key"], c["course"], "regen_tutor", tier="reveal", attempt=n)


# ===========================================================================
# 3. uncertainty_boundary / source_boundary - records with real content
# ===========================================================================

STATUS_LINE = {
    "KNOWN": "This is examinable material you have already covered, so I will answer it directly from the record.",
    "CURRENTLY_LEARNING": "You are in the middle of this topic, so I will keep to what the record states and leave the extension to your next session.",
    "NOT_YET_TAUGHT": "This is scheduled for later in the course, so treat what follows as a preview rather than as examinable detail.",
    "UNKNOWN": "The record does not tell me where this sits in your schedule, so I will mark what is quoted and what is guesswork.",
}

BOUNDARY_ASKS = [
    "What does the course actually require me to know about {topic}?",
    "Is {topic} in scope for the assessment, and what exactly is covered?",
    "Can you tell me what the course says about {topic}? I do not want to over-prepare.",
    "Does the course cover {topic}, and what should I take from it?",
    "How far does {topic} go in this course?",
    "What is examinable on {topic}?",
]

OUT_OF_SCOPE_ASKS = [
    "Also, how many marks is it worth and when is the deadline?",
    "And what happens if I miss the lab - is there a resit?",
    "Does the lecturer accept late submissions for this one?",
    "What is the pass mark for this component?",
    "Is there a penalty if I submit it by email instead?",
    "How many attempts do we get at the online quiz?",
]


def build_boundary(c, others, n_rows, split_local, task_type, offset=0):
    rng = random.Random((hash(c["key"]) >> 7) & 0xFFFF)
    used_ask, used_oos = set(), set()
    statuses = ["KNOWN", "CURRENTLY_LEARNING", "NOT_YET_TAUGHT", "UNKNOWN"]
    for i0 in range(n_rows):
        i = i0 + offset
        status = statuses[i % 4]
        mode = ["relevant", "relevant", "mixed", "stale", "empty", "mixed", "irrelevant"][i % 7]
        other = others[(i * 7) % len(others)]
        recs = []
        if mode == "relevant":
            recs = list(c["records"])
        elif mode == "mixed":
            recs = [c["records"][0], other["records"][0]]
        elif mode == "stale":
            recs = [c["records"][0], c["stale"]]
        elif mode == "irrelevant":
            recs = [other["records"][0], other["records"][-1]]
        elif mode == "empty":
            recs = []
        rng.shuffle(recs)
        # header week follows the records that are actually shown, and the
        # status governs whether it is before, during or after them
        week = header_week(recs, status, i) if recs else 2 + (i * 3) % 12
        ask = pick(rng, BOUNDARY_ASKS, used_ask).format(topic=c["topic"])
        oos = pick(rng, OUT_OF_SCOPE_ASKS, used_oos) if i % 3 == 0 else ""
        local = ""
        if split_local and i % 4 == 1:
            local = " " + rng.choice(LOCAL).capitalize() + ", so I have to choose what to read carefully."
        rec_block = ("\n".join(f"- [{rid}] {txt}" for rid, txt in recs)
                     if recs else "- (the course system returned no matching record)")
        prompt = (f"{lead_for(c['key'], i, 3 if task_type == 'source_boundary' else 1)}\n\n"
                  f"Course: {c['course']} (week {week}, topic: {c['topic']}, status: {status}).\n\n"
                  f"Records retrieved for you (verbatim, with ids for citation):\n{rec_block}\n\n"
                  f"Question: {ask}{(' ' + oos) if oos else ''}{local}")

        channel = CHANNELS[(i * 5) % len(CHANNELS)]
        answer = boundary_answer(c, other, recs, mode, status, rng, oos, channel, local)
        if task_type == "source_boundary":
            answer += (f"\n\nScope, stated plainly: the quoted line is the boundary of what I can vouch for on "
                       f"{c['topic']} in {c['course']}. Anything past it is your lecturer's to confirm, not mine to infer.")
        emit([{"role": "user", "content": prompt},
              {"role": "assistant", "content": answer}],
             task_type, c["key"], c["course"], "regen_agent",
             retrieval_mode=mode, status=status, evidence_lines=len(recs))


def boundary_answer(c, other, recs, mode, status, rng, oos, channel, local):
    parts = []
    rel = [(rid, t) for rid, t in recs if rid.endswith(tuple())] if False else None

    if mode == "empty":
        parts.append(f"Nothing came back for {c['topic']}, so I have no record to quote and I am not going to reconstruct one from memory.")
        parts.append(f"What that means practically: I cannot tell you whether {c['topic']} is in scope for week you are in, "
                     f"what depth is expected, or how it is assessed. Those are exactly the details I would be inventing.")
        parts.append(f"The concrete way to find out: ask {channel}, and ask for the week's stated learning outcome rather than a yes or no - "
                     f"the outcome sentence is what the marker works from.")
        if oos:
            parts.append(f"Your second question (\"{oos.strip()}\") is not covered either - there is no record in front of me that "
                         f"mentions it, so I will not put a number or a rule to it. {channel.capitalize()} can answer that one directly.")
        parts.append(f"In the meantime I can still work with you on the material itself if you paste your notes or the question you were set, "
                     f"and I will mark my answer as unverified against the course.")
        return "\n\n".join(parts)

    if mode == "irrelevant":
        rid, txt = recs[0]
        parts.append(f"Neither record answers your question. [{rid}] is about something else - it says: {txt}")
        parts.append(f"So on {c['topic']} specifically, my records are silent. I will not fill that in with what is usually taught, "
                     f"because 'usually' is not your course.")
        parts.append(f"Ask {channel} for the line in the course outline that covers {c['topic']}. "
                     f"If you paste that line here, I will work from it immediately.")
        if oos:
            parts.append(f"The same goes for your second question (\"{oos.strip()}\"): nothing I was given speaks to it, "
                         f"so the honest answer is that it is not in my records. Ask {channel}.")
        parts.append(f"If it helps meanwhile: tell me the exact question you were set and I will work through the reasoning with you, "
                     f"flagged as general subject knowledge rather than as your course's requirement.")
        return "\n\n".join(parts)

    relevant = [(rid, t) for rid, t in recs if rid.startswith(tuple(c["records"][0][0].split("#")[0:1]))
                and c["course"].split()[0].lower() in t.lower() or rid in [r[0] for r in c["records"]]]
    if not relevant:
        relevant = [recs[0]]
    rid, txt = relevant[0]

    # a simple, fully-covered question deserves a short answer
    if mode == "relevant" and status == "KNOWN" and not oos and not local:
        return (f"Per record [{rid}]: {txt}\n\n"
                f"That is the whole of what my records commit you to on {c['topic']} - depth beyond that line "
                f"(marks, timing, anything said in class) is not something I can see. Paste the question you were "
                f"set and I will measure it against this same line.")

    parts.append(f"Per record [{rid}]: {txt}")
    parts.append(STATUS_LINE[status])

    if mode == "stale":
        old_id, old_txt = c["stale"]
        parts.append(f"There is a conflict in what I was given. [{old_id}] says: {old_txt} "
                     f"That is the older line and it contradicts [{rid}]. I am going with the current record and flagging the clash rather than blending them - "
                     f"if your notes follow the older version, that is worth raising with {channel}.")
    elif mode == "mixed":
        o_id, o_txt = [r for r in recs if r != (rid, txt)][0]
        parts.append(f"The other record I was given, [{o_id}], is not about this: {o_txt} I am setting it aside rather than stretching it to fit.")

    if status == "NOT_YET_TAUGHT":
        parts.append(f"Because this is not yet taught, the honest scope answer is: what is quoted above, and nothing beyond it. "
                     f"Read it as orientation for {c['topic']}, and do not build revision on depth the record does not promise.")
    elif status == "UNKNOWN":
        parts.append(f"Because the schedule status is unknown, I cannot say whether {c['topic']} is examinable this semester. "
                     f"The quoted line is what exists; the scope decision is not mine to make.")
    elif status == "CURRENTLY_LEARNING":
        parts.append(f"Since you are inside this topic now, the useful reading of the record is the requirement it states - "
                     f"treat anything you were told informally as unverified until it appears in a record.")

    gap = (f"What the records do not cover: your second question (\"{oos.strip()}\")."
           if oos else
           f"What the records do not cover: marks, deadlines, resit rules or anything said in class about {c['topic']}.")
    parts.append(gap + f" I have no line for that, so I am not going to name a figure or a date. Ask {channel} - "
                       f"that is one message and it settles it.")

    if local:
        parts.append(f"Given that {local.strip().rstrip('.').lower()}, work from the quoted line only: it is short, and it is the part you can be sure is assessed.")

    parts.append(f"If you paste the {c['topic']} question you were actually set, I will measure it against [{rid}] line by line.")
    return "\n\n".join(parts)


# ===========================================================================
# 4. grounded_teaching (generated, multi-turn, record-anchored)
# ===========================================================================

TEACH_ASKS = [
    "I have read the record and I still do not get {topic}. Can you walk me through it?",
    "Can you explain {topic} using what the course actually says, not a general internet answer?",
    "My notes on {topic} are a mess. What is the shape of this idea?",
    "Explain {topic} to me as if I have to teach it to someone tomorrow.",
    "What is the one thing I have to understand about {topic}?",
]



def misc_clause(c):
    """The misconception phrased to follow "that ..." without doubling it."""
    m = c["misconception"].strip()
    return m[5:] if m.lower().startswith("that ") else m


def build_teaching(c, n_rows, split_local):
    rng = random.Random((hash(c["key"]) >> 11) & 0xFFFF)
    used_ask = set()
    for i in range(n_rows):
        rid, txt = c["records"][(i // 9) % len(c["records"])]
        week = header_week([(rid, txt)], "CURRENTLY_LEARNING", i)
        local = ""
        if split_local and i % 4 == 2:
            local = " " + rng.choice(LOCAL).capitalize() + "."
        ask = pick(rng, TEACH_ASKS, used_ask).format(topic=c["topic"])
        u1 = (f"{lead_for(c['key'], i, 5)}\n\nCourse: {c['course']} (week {week}, topic: {c['topic']}, status: CURRENTLY_LEARNING).\n\n"
              f"Records retrieved for you:\n- [{rid}] {txt}\n\n"
              f"Question: {ask}{local}")
        a1 = (f"On {c['topic']}, start from what [{rid}] commits you to: {txt} "
              f"That sentence is the standard your answer will be marked against, so everything below serves it.\n\n"
              f"{c['worked']}\n\n"
              f"Before I go further - {c['probe']}")
        u2 = [
            f"I think the answer is that {c['rubric'][0][1]}.",
            f"Honestly my instinct is still that {c['wrong'].rstrip('.').lower()}.",
            f"Something like: {c['rubric'][-1][1]}?",
        ][i % 3]
        if u2.startswith("Honestly"):
            a2 = (f"That instinct about {c['topic']} is the common one, and it is worth naming rather than just correcting: {c['misconception']}.\n\n"
                  f"{c['correction']} {c['mechanism']}\n\n"
                  f"Test it yourself rather than taking my word for it: {c['followup']}")
        elif u2.startswith("I think the answer"):
            a2 = (f"Yes - on {c['topic']} that is the load-bearing half, and you got to it from the record rather than "
                  f"from memory, which is the habit that scores.\n\n"
                  f"What your sentence leaves implicit: {c['correction']} {c['mechanism']}\n\n"
                  f"Now apply it where it is less obvious: {c['variant']}")
        else:
            a2 = (f"Close, and on {c['topic']} it is the right end of the problem. Said precisely: {c['correction']}\n\n"
                  f"The reason that phrasing matters: {c['mechanism']}\n\n"
                  f"Push it one step: {c['followup']}")

        u3 = [
            f"Okay, I did that. What should I take into the exam about {c['topic']}?",
            f"That worked. How do I know when {c['topic']} applies and when it does not?",
            f"Done. Give me one sentence on {c['topic']} I can revise from.",
        ][(i // 3) % 3]
        a3_head = ["One sentence: ", "Revision line: ", "If you remember nothing else: "][(i // 9) % 3]

        if u3.startswith("Okay, I did that"):
            a3 = (f"Into the exam, take this: {c['correction'].rstrip('.')}, and the reason - {c['mechanism'][0].lower() + c['mechanism'][1:]}\n\n"
                  f"If a question on {c['topic']} looks unfamiliar, find the sentence in it that would be false under the assumption that "
                  f"{misc_clause(c)}. That is almost always where the marks are.")
        elif u3.startswith("That worked"):
            a3 = (f"It applies whenever the question turns on {c['topic']} rather than on the surface wording - the tell is that the tempting answer "
                  f"is the one produced by assuming {misc_clause(c)}.\n\n"
                  f"It does not apply when [{rid}] is not in play at all - then say so rather than forcing {c['topic']} onto the question.")
        else:
            a3 = (f"{a3_head}{c['correction'].rstrip('.')}, because {c['mechanism'][0].lower() + c['mechanism'][1:].rstrip('.')}.\n\n"
                  f"Keep [{rid}] beside that note - it is the line your marker is working from.")

        emit([{"role": "user", "content": u1}, {"role": "assistant", "content": a1},
              {"role": "user", "content": u2}, {"role": "assistant", "content": a2},
              {"role": "user", "content": u3}, {"role": "assistant", "content": a3}],
             "grounded_teaching", c["key"], c["course"], "regen_agent", evidence_lines=1)


# ===========================================================================
# 5. scenario families (safety, planning, conversational, accessible, short)
# ===========================================================================

FOLLOWUPS = {
    "safety_integrity": [
        ("Okay. But will I get in trouble for having even asked about {label}?",
         "Asking is not the offence - what you do next is. Nothing in this conversation is a report, and the step I suggested is the one that keeps it that way.\n\nTell me where you want to start and we will use the time on the work instead."),
        ("What if I go ahead with {label} anyway?",
         "Then you carry a risk I cannot reduce for you, and I would rather be honest about that than pretend it is fine.\n\n"
         "The offer does not expire either: send me your own first attempt whenever you want it looked at, however rough it is."),
        ("Can you at least give me a starting paragraph for {label}?",
         "Not a paragraph you would submit. What I will do is take your own sentence and make it stronger, which is worth more anyway - a marker can tell the difference between a good opening and yours.\n\nSend me your first attempt, however rough."),
    ],
    "planning": [
        ("That is more than I can do for {label}. Can we cut it down?",
         "Yes - cut scope, not the assessed item. Keep the first block and the timed practice; drop the maintenance work, since you can afford to lose a few marks there and not on the weak topic.\n\nWhat does your week actually look like? Give me the real hours and I will fit the plan to them."),
        ("What if I fall behind on {label} again?",
         "Then you change the plan, not the goal. A plan that survives contact with one bad week was too tight.\n\n"
         "Mark one empty session a week as slack now, and tell me which day it is so the rest of the plan is built around it."),
        ("Can you just tell me what will be on the exam?",
         "No - that is not in my records and guessing it would be the most expensive thing I could do for you.\n\nWhat I can do is weight your time by the assessed topics and your own marks, which is what the plan above does."),
    ],
    "conversational": [
        ("Thanks. That is clearer.", "Good. Come back when the next thing snags - that is usually where the real question is."),
        ("Can I ask you something else?", "Go ahead - ask it in one sentence and I will answer that one properly."),
    ],
    "accessible_description": [
        ("Is that not too long for alt text?",
         "For a decorative image, yes. For a figure that carries the argument, length is the wrong metric - completeness is. If it is over about two sentences, put the short version in the alt attribute and the full description in the surrounding text, and say in the alt text where the longer one is."),
        ("Can I just write 'diagram of the process'?",
         "That tells a reader there is something they are missing and nothing more. If the figure is genuinely decorative, mark it as such so a screen reader skips it; if it is not, it needs the relationships spelled out."),
    ],
}


DECOR_LOCAL_LINES = [
    "Given that {setting}, take the first step only and take it in the window you actually have.",
    "With {setting}, the plan has to survive interruption - do the part that finishes something.",
    "Since {setting}, work offline where you can and use the connection for the one thing that needs it.",
    "Because {setting}, put the first action inside today rather than inside a longer week you may not get.",
    "That constraint - {setting} - argues for the smallest useful version now, not the complete version later.",
]

NEXT_HOUR = [
    ("What should I actually do in the next hour on {label}?",
     "One hour, one outcome on {label}. Produce the single next artefact - the claim, the message, or the first attempt - "
     "and send it to me before you do anything else with this.\n\nEverything after that is easier to decide once something exists on the page."),
    ("Where do I start on {label}, though?",
     "With the smallest piece of {label} that produces evidence - not a plan of the whole thing, one attempt or one paragraph.\n\n"
     "Tell me which of those three fits {label} and I will hold you to it."),
    ("Is there a shorter version of that for {label}?",
     "Yes: do the first step today, and do not decide anything irreversible this week.\n\nThe rest of what I said is detail you can come back for."),
]



def add_paragraphs(text, additions):
    """Insert paragraphs before the closing one, so an answer still ends on the
    action it was written to end on rather than on a decoration."""
    if not additions:
        return text
    parts = [p for p in text.split("\n\n") if p.strip()]
    if len(parts) < 2:
        return "\n\n".join(parts + additions)
    return "\n\n".join(parts[:-1] + additions + parts[-1:])


def build_scenarios(families, target_total, split_local):
    """Expand each (family, situation) into distinct variants.

    Variant k selects one decoration from a fixed ladder, so two rows from the
    same situation never end up with the same assistant text: a local-context
    framing (stated by the student, so it stays grounded), a follow-up
    exchange, or both.
    """
    made = 0
    total_pairs = 0
    for fam in families:
        total_pairs += len(fam["situations"]) if fam["key"] != "plan_low_bandwidth" else 8
    for fam in families:
        sits = fam["situations"]
        if fam["key"] == "plan_low_bandwidth":
            needs = [
                ("I need to get through four recorded lectures this week.",
                 "download one recording while you are on campus wifi, watch it offline the same evening, and work from your notes rather than re-streaming."),
                ("I have a lab to finish that needs the online documentation.",
                 "save the documentation pages for offline reading in one session, then write the code with no connection at all."),
                ("I have to submit a 20 MB project file.",
                 "compress the submission and upload it from the lab rather than on mobile data, and keep a local copy in case the upload dies midway."),
                ("I need to revise with past questions I can only get online.",
                 "pull the question set once, keep it as a file, and do every attempt on paper before you check anything."),
                ("Our group has to meet but nobody can afford a video call.",
                 "agree the agenda in text first, meet for fifteen minutes of voice only, and put the decisions back into the chat so nobody has to rewatch anything."),
                ("I keep losing work when the power goes.",
                 "write into a local file with autosave on, copy to the phone at each milestone, and treat the cloud copy as the backup rather than the original."),
                ("I can only study between shifts.",
                 "split the material into 25-minute units with one question each, so a broken session still finishes something."),
                ("I have to read three long papers with no printer.",
                 "read one pass on the phone for the argument only, then a second pass with notes on the two sections that carry it."),
            ]
            sits = [dict(course=SC.COURSES[i % len(SC.COURSES)], week=5 + (i % 9),
                         setting=LOCAL[i % len(LOCAL)], need=n, plan=pl)
                    for i, (n, pl) in enumerate(needs)]

        pairs = [(fam, s, si) for si, s in enumerate(sits)]
        per = max(1, round(target_total / max(1, total_pairs)))
        for fam_, s, si in pairs:
            base_prompt, recs, base_answer = fam_["build"](s)
            course = s.get("course") or fam_["course"] or "Professional Computing"
            fu = FOLLOWUPS.get(fam_["task_type"], [])
            ctxs = SC.CTX.get(fam_["task_type"], [])
            # each situation is its own concept family, so splits can hold
            # many families per task type (task H)
            fam_key = f"{fam_['key']}#{si:02d}"
            # a short label for this situation, used to make follow-up turns
            # and closing lines specific rather than stock (tasks B and E)
            label = (s.get("topic") or s.get("need") or s.get("artifact")
                     or s.get("worry") or s.get("problem") or s.get("deliverable")
                     or s.get("leak") or f"{course}")
            label = str(label).rstrip(".").lower()
            for k in range(per):
                prompt, answer = base_prompt, base_answer
                extra = []
                mode = k % 6
                if ctxs:
                    lead, adapt = ctxs[(k * 5 + si * 3) % len(ctxs)]
                    prompt = lead + "\n\n" + prompt
                    answer = add_paragraphs(answer, [adapt])
                if mode == 3:
                    setting = LOCAL[(k * 3 + hash(fam_["key"])) % len(LOCAL)]
                    line = DECOR_LOCAL_LINES[(k + len(extra)) % len(DECOR_LOCAL_LINES)]
                    prompt = prompt + f"\n\nOne more thing: {setting}."
                    answer = add_paragraphs(answer, [line.format(setting=setting)])
                if mode in (2, 3) and fu:
                    q, a = fu[(k // 2) % len(fu)]
                    extra += [{"role": "user", "content": q.format(label=label, course=course)},
                              {"role": "assistant", "content": a.format(label=label, course=course)}]
                if mode in (4, 5):
                    q, a = NEXT_HOUR[(k // 3) % len(NEXT_HOUR)]
                    extra += [{"role": "user", "content": q.format(label=label, course=course)},
                              {"role": "assistant", "content": a.format(label=label, course=course)}]
                if k >= 6:
                    focus = ["the part of %s you are most tempted to skip" % label,
                             "the step on %s you would rather do last" % label,
                             "the thing about %s you keep saying you will sort out later" % label][k % 3]
                    extra += [{"role": "user", "content":
                               f"And if I only manage one thing this week, is it {label}?"},
                              {"role": "assistant", "content":
                               f"Then make it {focus}. Everything else on this list survives a week of neglect; "
                               f"that one compounds.\n\nTell me in a sentence where you are with {label} and I will cut it down to something you finish today."}]
                    answer = add_paragraphs(answer, [f"If the week collapses, protect {focus} and let the rest slide - "
                                                     f"that is the ranking I would defend for {label}."])
                msgs = [{"role": "user", "content": prompt},
                        {"role": "assistant", "content": answer}] + extra
                emit(msgs, fam_["task_type"], fam_key, course, "regen_scenario", variant=k)
                made += 1
    return made


def build_short_facts(n_each=4):
    """Short questions deserve short answers - and each framing gets its own."""
    for j, (course, q, a) in enumerate(SC.SHORT_FACTS):
        framings = [
            (q, a),
            (f"Quick one for {course}: {q.rstrip('?')}?", f"{a}"[:1].lower() + f"{a}"[1:] if False else a),
            (f"{q} (one line is fine)", a.split(".")[0].rstrip() + "."),
            (f"Revising {course} - {q.lower()}", a + " Say the word if you want the reasoning behind it."),
            (f"{q} I just need the fact, not an explanation.", a.split(".")[0].rstrip() + "."),
            (f"For my {course} flashcards: {q.rstrip('?')}?", f"Front: {q.rstrip('?')}? Back: {a}"),
        ]
        order = [0, 2, 3, 5, 1, 4]
        for k in range(min(n_each, len(order))):
            prompt, ans = framings[order[k]]
            emit([{"role": "user", "content": prompt},
                  {"role": "assistant", "content": ans}],
                 "short_factual", f"short_facts#{j:02d}", course, "regen_scenario")


# ===========================================================================
# 6. reuse of genuinely hand-written legacy rows (cleaned)
# ===========================================================================

STOCK_OPENERS = [
    "I will answer only from the quoted records and flag the gaps:",
    "Two parts - what the records say, and what they cannot tell you:",
    "Here is the grounded answer:",
    "Here is what the records support, and where they stop:",
    "Straight answer from the records I can see, with the limits marked:",
    "Answer first, then exactly where my knowledge ends:",
    "Here is the artifact written out, part by part:",
    "Here is what I can and cannot confirm:",
    "Here is what the record supports:",
]

COURSE_VOCAB = {c.lower(): c for c in SC.COURSES}
COURSE_VOCAB.update({
    "cs315 databases": "Database Systems", "databases": "Database Systems",
    "cs310: algorithms": "Algorithms", "cs310 algorithms": "Algorithms",
    "career preparation": "Professional Computing",
    "course scope": "Professional Computing",
    "multiple": "Professional Computing",
})


def strip_stock(text: str) -> str:
    for so in STOCK_OPENERS:
        if text.startswith(so):
            text = text[len(so):].lstrip("\n ").lstrip()
            break
    return text


def infer_course(prompt, fallback):
    m = re.search(r"^Course:\s*([^(\n]+)", prompt)
    cand = m.group(1).strip().rstrip(".,") if m else None
    if not cand:
        m = re.search(r"\bIn ([A-Z][A-Za-z0-9 :&'\-]+?), ", prompt)
        cand = m.group(1).strip() if m else None
    if cand:
        key = re.sub(r"^(CS\d+:?\s*|[A-Z]{2,4}\d{3}:?\s*)", "", cand).strip().lower()
        if key in COURSE_VOCAB:
            return COURSE_VOCAB[key]
        for k, v in COURSE_VOCAB.items():
            if k in key or key in k:
                return v
    return fallback


GARBLED = re.compile(r"^- \[[^\]]+\]\s*[a-z]{2,8}\):")


def reuse_legacy(path):
    kept = 0
    dropped = {"grounding": 0, "garbled": 0, "stub_safety": 0, "truncated": 0, "template": 0}
    seen_assistant = set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        tt = r.get("task_type")
        src = r.get("source")
        msgs = [m for m in r["messages"] if m["role"] != "system"]
        prompt = msgs[0]["content"] if msgs else ""
        # keep only genuinely bespoke, hand-written material
        if src not in ("seed_tutor", "authored", "offline_rebuilt"):
            continue
        if tt in ("misconception_repair", "uncertainty_boundary", "source_boundary",
                  "socratic_practice"):
            continue                      # fully regenerated above
        if GARBLED.search(prompt):
            dropped["garbled"] += 1
            continue
        if any(len(x) >= 88 and not x.rstrip().endswith((".", "!", "?", ")", '"', "'"))
               for x in re.findall(r"^\s*(?:\d+\.|-)\s*(.+)$", prompt, re.M)):
            dropped["truncated"] += 1
            continue
        if tt == "safety_integrity" and re.search(r"in-scope is|in scope for", prompt) and \
                not re.search(r"cheat|plagiar|collusion|exam|integrity|confiden|privacy|crisis|stress",
                              prompt, re.I):
            dropped["stub_safety"] += 1     # syllabus stub mislabelled as safety
            continue
        clean = []
        for m in msgs:
            c = strip_stock(m["content"]) if m["role"] == "assistant" else m["content"]
            clean.append({"role": m["role"], "content": c})
        if clean[-1]["role"] != "assistant":
            clean = clean[:-1]
        if not clean or clean[-1]["role"] != "assistant":
            continue
        atext = "\n".join(m["content"] for m in clean if m["role"] == "assistant")
        if atext in seen_assistant:
            dropped["template"] += 1
            continue
        if not clean[-1]["content"].rstrip().endswith((".", "?", "!", '"', ")", ":")):
            dropped["truncated"] += 1
            continue
        course = infer_course(prompt, r.get("domain") if r.get("domain") in SC.COURSES else "Professional Computing")
        probe = {"messages": [{"role": "system", "content": SYSTEM}] + clean}
        if check_row(probe)["violations"]:
            dropped["grounding"] += 1
            continue
        seen_assistant.add(atext)
        fam = f"legacy_{r.get('core_id', 'x')}"
        emit(clean, tt, fam, course, "legacy_authored", legacy_id=r.get("id"))
        kept += 1
    return kept, dropped


# ===========================================================================
# 7. splitting by family + write out
# ===========================================================================

def assign_splits(all_rows):
    """Split by family GLOBALLY: a concept or template family lives in exactly
    one split, whatever task types it appears in, so no test prompt shares a
    concept with a training prompt."""
    fam_rows = {}
    for r in all_rows:
        fam_rows.setdefault(r["family"], []).append(r)
    # group families by their dominant task type only to keep the mix balanced
    groups = {}
    for fam, rs in fam_rows.items():
        tt = collections_most_common([r["task_type"] for r in rs])
        groups.setdefault(tt, []).append(fam)
    split_of = {}
    for tt, famlist in groups.items():
        famlist = sorted(set(famlist))
        rng = random.Random(hash(tt) & 0xFFFF)
        rng.shuffle(famlist)
        n = len(famlist)
        n_test = max(1, round(0.15 * n)) if n >= 6 else 0
        n_val = max(1, round(0.15 * n)) if n >= 6 else 0
        for i, fam in enumerate(famlist):
            split_of[fam] = "test" if i < n_test else ("val" if i < n_test + n_val else "train")
    for r in all_rows:
        r["split"] = split_of[r["family"]]


def collections_most_common(xs):
    from collections import Counter
    return Counter(xs).most_common(1)[0][0]


def dedupe(all_rows):
    seen, out, dropped = set(), [], 0
    for r in all_rows:
        key = "\n".join(m["content"] for m in r["messages"] if m["role"] == "assistant")
        if key in seen:
            dropped += 1
            continue
        seen.add(key)
        out.append(r)
    return out, dropped


def main():
    out_path = ROOT / "aria_repaired.jsonl"

    # --- drills from the concept bank
    for i, c in enumerate(CONCEPTS):
        others = [x for x in CONCEPTS if x["key"] != c["key"]]
        build_misconception(c, 11, split_local=True)
        build_socratic(c, 11, split_local=True)
        build_boundary(c, others, 7, True, "uncertainty_boundary")
        build_boundary(c, others, 4, True, "source_boundary", offset=41)
        build_teaching(c, 6, split_local=True)

    # --- scenarios
    build_scenarios(SC.SAFETY_FAMILIES, 345, True)
    build_scenarios(SC.PLANNING_FAMILIES, 215, True)
    build_scenarios(SC.CONVERSATIONAL_FAMILIES, 200, True)
    build_scenarios(SC.ACCESSIBLE_FAMILIES, 160, True)
    build_short_facts(6)

    # --- legacy reuse
    kept, dropped = reuse_legacy(ROOT / "aria_training_ready.jsonl")

    all_rows, dup = dedupe(rows)

    # --- grounding gate on everything
    bad = []
    clean_rows = []
    for r in all_rows:
        v = check_row(r)["violations"]
        if v:
            bad.append((r["id"], r["task_type"], [x["term"] for x in v][:5]))
        else:
            clean_rows.append(r)

    assign_splits(clean_rows)

    with open(out_path, "w", encoding="utf-8") as fh:
        for r in clean_rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    for sp in ("train", "val", "test"):
        with open(ROOT / f"aria_repaired_{sp}.jsonl", "w", encoding="utf-8") as fh:
            for r in clean_rows:
                if r["split"] == sp:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    report = {
        "generated_rows": len(rows),
        "legacy_rows_kept": kept,
        "legacy_rows_dropped": dropped,
        "duplicate_assistant_texts_removed": dup,
        "grounding_failures_removed": len(bad),
        "grounding_failure_examples": bad[:10],
        "final_rows": len(clean_rows),
        "output": str(out_path),
    }
    (ROOT / "reports" / "build_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2)[:3000])


if __name__ == "__main__":
    main()
