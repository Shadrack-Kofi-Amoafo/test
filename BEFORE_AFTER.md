# Ten before/after pairs (round 1 -> round 2)

`before` rows are from commit `41ecc6c` (the file you reviewed); `after` rows are from the current `aria_repaired.jsonl`.

## 1. grounded_teaching opener (5.78% of turns -> concept-specific)

**Before — R00060**

```
Start from what the record commits you to. [lecture#infosec-w7-hashing] says: Week 7 lecture note: password storage must use a deliberately slow KDF; general-purpose hashes are rejected in this course's marking scheme. That sentence is the standard your answer will be marked against, so everything b
```

**After — R00034**

```
On password storage, start from what [lecture#infosec-w7-hashing] commits you to: Week 7 lecture note: password storage must use a deliberately slow KDF; general-purpose hashes are rejected in this course's marking scheme. That sentence is the standard your answer will be marked against, so everythi
```

## 2. scenario follow-up turn (10.38% of follow-ups -> situation-specific)

**Before — R03181**

```
And if I only manage one thing this week?
```

**After — R03517**

```
And if I only manage one thing this week, is it ethics case analysis?
```

## 3. accessible_description first line (15 distinct over 150 rows -> one per context)

**Before — R03913**

```
Course: Database Systems (week 6, topic: entity-relationship diagrams, status: KNOWN).

Question: I need alt text for the entity-relationship diagram for the library schema in our Database Systems slides. The boxes are labelled Member, Loan and Book, and the t
```

**After — R04249**

```
This is going into a slide deck I present on Thursday.

Course: Database Systems (week 6, topic: entity-relationship diagrams, status: KNOWN).

Question: I need alt text for the entity-relationship diagram for the library schema in our Database Systems slides.
```

## 4. conversational first line (22 distinct over 198 rows -> one per situation)

**Before — R03718**

```
I am halfway through the degree and I still cannot tell whether I want to build software or work with data. Any thoughts?

One more thing: the hostel network in Kumasi drops every evening around eight.
```

**After — R04054**

```
I think I chose this degree for the wrong reasons.

I am halfway through the degree and I still cannot tell whether I want to build software or work with data. Any thoughts?

One more thing: I do night shifts at a pharmacy in Tema and study after.
```

## 5. week vs record contradiction (150 rows -> 0)

**Before — R00042**

```
Course: Information Security (week 2, topic: password storage, status: KNOWN).

Records retrieved for you (verbatim, with ids for citation):
- [lab#infosec-w7-brief] Lab 7 brief: implement registration and login with bcrypt, and report the cost factor you chose and why.
- [lecture#infosec-w7-hashing] Week 7 lecture note: password storage must use a deliberately slow KDF; general-purpose hashes are
```

**After — R00023**

```
I read the slides twice and still cannot use this.

Course: Information Security (week 7, topic: password storage, status: KNOWN).

Records retrieved for you (verbatim, with ids for citation):
- [lab#infosec-w7-brief] Lab 7 brief: implement registration and login with bcrypt, and report the cost factor you chose and why.
```

## 6. second question unanswered (46 rows -> 1)

**Before — R00048**

```
ng] Week 3: reports must describe the sampling frame and the recruitment channel, and name who is excluded.

Question: What is examinable on password storage? What is the pass mark for this component?
```

**After — R00023**

```
ens if I miss the lab - is there a resit?"). I have no line for that, so I am not going to name a figure or a date. Ask the course page announcements - that is one message and it settles it.

If you paste the password storage question you were actually set, I will measure it against [lab#infosec-w7-brief] line by line.
```

## 7. local context (10 settings, 'cedi' in 4.1% of rows -> 30 settings, none over 2%)

**Before — R03238**

```
opened it. Half the group chat has already replied asking for it. What should I do?

One more thing: I study on a shared laptop in the departmental lab in Cape Coast and only get about an hour on it.
```

**After — R03724**

```
eek and I cannot think straight. Part of me wants to withdraw from the semester. I do not know what to ask you for.

One more thing: I am in Bolgatanga this semester and the bus back takes a full day.
```

## 8. student answers within one concept (repeats -> 10 distinct of 11 rows, 53 available)

**Before — sec_password_storage (old)**

```
Each account gets its own random salt, so one precomputed table cannot cover eve
MD5 and SHA-256 are built to be fast, so a cracker can test billions of candidat
MD5 is fine here because it is one-way. Hash the password twice and keep the dat
Passwords should be at least twelve characters and include a symbol.
```

**After — sec_password_storage (new)**

```
Each account gets its own random salt, so one precomputed table cannot cover eve
MD5 and SHA-256 are built to be fast, so a cracker can test billions of candidat
MD5 is fine here because it is one-way. Hash the password twice and keep the dat
The cost parameter has to be raised as hardware gets faster. store the value wit
```

## 9. doubled conjunction found in Stage J review (fixed at source)

**Before — R00060**

```
...false under the assumption that that an index is a free speed setting...
```

**After — R00034**

```
...ption that a password hash is judged by how unbreakable the algorithm sounds, when the property that matters is how slow it is per guess. That is almost always where the marks are.
```

## 10. socratic close (stock string -> verdict + the concept's own correction)

**Before — R00021**

```
That is it. Say it once more in your own words with the condition attached - Replace the fast hash with bcrypt or Argon2 at a tuned cost factor, and give every account its own random salt - and it will survive the exam.

One transfer task so it sticks: A colle
```

**After — R00013**

```
On password storage, that is it: Replace the fast hash with bcrypt or Argon2 at a tuned cost factor, and give every account its own random salt. Say it once more in your own words and it will survive the exam.

One transfer task so it sticks: A colleague sugge
```

