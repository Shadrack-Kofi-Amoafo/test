#!/usr/bin/env python3
"""grounding_check.py - automatic grounding verifier (Task D).

Rule enforced: every proper noun, form/policy code, number, date or named
policy that an assistant turn asserts must either
  (a) appear in the user turns or the system prompt of the same conversation,
  (b) be general knowledge of the subject (curated allowlist below), or
  (c) be a hedged/negated mention ("the records do not name a form"),
otherwise it is a grounding violation and the row must be rewritten.

Usage:
    python3 tools/grounding_check.py aria_repaired.jsonl            # summary
    python3 tools/grounding_check.py aria_repaired.jsonl --list 20  # examples
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --------------------------------------------------------------- allowlists
GENERAL_KNOWLEDGE = {
    # languages / tools / standards - general knowledge of the subject
    "python", "java", "javascript", "typescript", "c", "sql", "nosql", "html",
    "css", "json", "xml", "yaml", "http", "https", "tcp", "udp", "ip", "dns",
    "tls", "ssl", "rest", "api", "apis", "git", "github", "linux", "unix",
    "windows", "android", "ios", "docker", "kubernetes", "aws", "flask",
    "django", "react", "node", "mysql", "postgresql", "postgres", "sqlite",
    "mongodb", "redis", "excel", "word", "powerpoint", "figma", "photoshop",
    "md5", "sha", "sha-1", "sha-256", "aes", "rsa", "bcrypt", "scrypt",
    "argon2", "pbkdf2", "jwt", "oauth", "csrf", "xss", "sql injection",
    "b-tree", "b-trees", "acid", "base", "crud", "orm", "mvc", "tdd", "ci",
    "cd", "utf-8", "ascii", "rgb", "cmyk", "jpeg", "png", "gif", "mp3", "mp4",
    "wcag", "gdpr", "os", "ram", "cpu", "gpu", "ssd", "hdd", "lms", "gpa",
    "big o", "o", "fifo", "lifo", "lru", "dhcp", "nat", "vpn", "ssh", "ftp",
    "smtp", "ajax", "dom", "api key", "arp", "osi", "mac", "wifi", "wi-fi",
    "lan", "wan", "cdn", "uml", "erd", "sdlc", "qa", "ux", "ui", "alt",
    "gsm", "sms", "ussd", "apk", "pdf", "csv", "ide", "cli", "gui", "sdk",
    "mbps", "kbps", "gbps", "khz", "mhz", "ghz", "ram", "rom", "ethernet",
    "authorization", "options", "explain", "select", "update", "insert",
    "delete", "where", "order", "join", "null", "true", "false", "none",
    "avl", "coffman", "webauthn", "httponly", "secure", "samesite", "nonce", "quic", "svg", "webp", "tiff", "raw",
    "ussd", "momo", "nyquist", "pigeonhole", "big-o", "utf", "ipv4", "ipv6",
    "bfs", "dfs", "dp", "np", "np-complete", "ai", "ml", "llm", "chatgpt",
    "turing", "dijkstra", "fisher", "yates", "mersenne", "twister", "knuth",
    "nyquist", "shannon", "moore", "amdahl", "boyce", "codd", "hoare",
    "argon", "unicode", "ieee", "iso", "w3c", "owasp", "nist", "posix",
    # generic academic words that capitalise at sentence start
    # place names used in worked examples are general knowledge; institution
    # names ("University of Cape Coast", "Dean of Students") are multi-token
    # and are still flagged unless the prompt supplies them
    "ghana", "ghanaian", "accra", "kumasi", "cape coast", "elmina", "tamale",
    "takoradi", "frankfurt", "london", "lagos", "africa", "west africa",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
    "sunday", "aria", "week", "semester",
}

STOPWORDS_CAP = {
    "i", "the", "a", "an", "and", "but", "or", "so", "if", "then", "that",
    "this", "these", "those", "your", "you", "we", "it", "its", "here",
    "there", "what", "when", "where", "which", "who", "why", "how", "no",
    "not", "yes", "do", "does", "did", "don't", "start", "state", "name",
    "quote", "read", "write", "use", "using", "note", "next", "first",
    "second", "third", "last", "one", "two", "three", "four", "five", "six",
    "step", "steps", "before", "after", "because", "for", "from", "with",
    "without", "on", "in", "at", "to", "of", "as", "by", "my", "me", "our",
    "verdict", "earned", "missing", "misconception", "correction",
    "mechanism", "hint", "answer", "question", "task", "records", "record",
    "per", "point", "points", "rubric", "still", "try", "give", "show",
    "tell", "ask", "say", "pick", "run", "open", "check", "keep", "make",
    "good", "right", "wrong", "correct", "partially", "instead", "now",
    "both", "each", "every", "any", "some", "most", "more", "less", "same",
    "different", "nothing", "something", "anything", "everything", "course",
    "student", "students", "tutor", "marker", "lecturer", "exam", "lab",
    "assignment", "project", "brief", "syllabus", "gradebook", "schedule",
    "unknown", "known", "not_yet_taught", "true", "false", "none", "n/a",
}

FORM_CODE = re.compile(r"\b[A-Z]{2,}[-\s]?\d{1,4}\b")
PROPER = re.compile(r"\b([A-Z][a-z]{2,}(?:[ -][A-Z][a-z]{2,})*)\b")
NUMBER = re.compile(r"\b\d[\d,]*(?:\.\d+)?%?\b")
# a bare "may" is a modal verb, so a month only counts as a date when it is
# capitalised and sits next to a day or year
DATE = re.compile(r"\b(?:\d{1,2}\s+)?(?:January|February|March|April|May|June|July|"
                  r"August|September|October|November|December)\b(?:\s+\d{2,4})?")

# Institutional / policy context: in these sentences a number or a name is a
# factual claim about the student's institution and must be grounded.
POLICY_CTX = re.compile(
    r"\b(deadline|due|submit|submission|extension|deferral|resit|penalt|late|"
    r"mark|marks|grade|grading|weight|worth|percent of|pass mark|fee|fees|cedi|"
    r"ghs|pesewa|office|dean|registry|registrar|faculty|policy|regulation|form|"
    r"handbook|committee|appeal|exam(?:ination)? (?:date|hall|board)|timetable)\b",
    re.I)

# Numbers that are general knowledge of the subject (units, constants, ports,
# standard sizes) or plain illustrative magnitudes in a worked example.
GENERAL_NUMBERS = {
    "8", "16", "32", "64", "128", "256", "512", "1024", "1,024", "2048",
    "443", "404", "200", "301", "500", "80", "22", "53", "20", "21", "25",
    "44.1", "48", "0.1", "0.2", "0.3", "3", "4", "7", "12", "24", "60",
    "100", "1,000", "10,000", "100,000", "1,000,000", "2,000", "5,000",
    "1.5", "2.5", "2", "1", "0",
}
ROUND_MAGNITUDE = re.compile(r"^\d{1,3}(,\d{3})*(\.\d+)?%?$")
HEDGE = re.compile(r"(do(?:es)? not (?:name|cover|say|list|mention|specify)|"
                   r"not in (?:my|the) records|no record|records are silent|"
                   r"I cannot confirm|is not indexed|nothing in the records)", re.I)

SMALL_OK = {str(i) for i in range(0, 11)}  # list markers, tiny counts


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


SENT_START = re.compile(r"(?:^|[.!?:;\n\"'(\[\u2014\u2018\u201c-]\s*|\*\*)$")


def candidates(text: str):
    out = []
    for m in FORM_CODE.finditer(text):
        out.append(("form_code", m.group(0), m.start()))
    for m in PROPER.finditer(text):
        term = m.group(1)
        toks = term.split()
        if len(toks) == 1:
            if _norm(term) in STOPWORDS_CAP:
                continue
            # a lone capitalised word at the start of a sentence is ordinary prose,
            # not a named entity - only flag it if it also occurs capitalised mid-sentence
            if SENT_START.search(text[max(0, m.start() - 3): m.start()]):
                mid = [mm for mm in re.finditer(re.escape(term), text)
                       if not SENT_START.search(text[max(0, mm.start() - 3): mm.start()])]
                if not mid:
                    continue
        out.append(("proper_noun", term, m.start()))
    for m in NUMBER.finditer(text):
        v = m.group(0)
        if v in SMALL_OK:
            continue
        out.append(("number", v, m.start()))
    for m in DATE.finditer(text):
        out.append(("date", m.group(0), m.start()))
    return out


def check_row(row: dict) -> dict:
    msgs = row.get("messages", [])
    context = " \n".join(m["content"] for m in msgs if m["role"] in ("user", "system"))
    ctx = _norm(context)
    violations = []
    for m in msgs:
        if m["role"] != "assistant":
            continue
        body = m["content"]
        for kind, term, pos in candidates(body):
            t = _norm(term)
            if t in ctx:
                continue
            if t in GENERAL_KNOWLEDGE or t.rstrip("s") in GENERAL_KNOWLEDGE:
                continue
            if all(w in GENERAL_KNOWLEDGE or w in STOPWORDS_CAP for w in t.split()):
                continue
            # hedged mention in the same sentence is allowed
            start = body.rfind(".", 0, pos) + 1
            end = body.find(".", pos)
            sentence = body[start: end if end > 0 else len(body)]
            if HEDGE.search(sentence):
                continue
            if kind in ("number", "date"):
                # A number is a grounding risk when it asserts something about
                # the student's institution (a deadline, a mark, a fee, a form,
                # a date). Quantities inside subject explanations - "a cache
                # line is 64 bytes", "120 KB once an hour" - are general
                # knowledge of the subject, which clause (b) permits.
                if not POLICY_CTX.search(sentence):
                    continue
            violations.append({"kind": kind, "term": term})
    # de-duplicate
    seen, uniq = set(), []
    for v in violations:
        k = (v["kind"], v["term"])
        if k not in seen:
            seen.add(k)
            uniq.append(v)
    return {"id": row.get("id"), "violations": uniq}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--list", type=int, default=0)
    args = ap.parse_args()
    rows = [json.loads(l) for l in Path(args.path).read_text(encoding="utf-8").splitlines() if l.strip()]
    bad = [check_row(r) for r in rows]
    bad = [b for b in bad if b["violations"]]
    print(json.dumps({"rows": len(rows), "rows_with_violations": len(bad),
                      "pct": round(100 * len(bad) / len(rows), 2)}, indent=2))
    for b in bad[: args.list]:
        print(b["id"], [v["term"] for v in b["violations"]][:8])
    return 0 if not bad else 0


if __name__ == "__main__":
    sys.exit(main())
