# -*- coding: utf-8 -*-
"""Scenario families for the non-drill task types.

Each family is a *template family* (the split unit): a situation, a set of
concrete slot fillings, one or more prompt phrasings and a response written
for that situation. Every specific the response names (a course, an artefact,
a channel, a date) is supplied by the prompt or by a quoted record, so the
grounding verifier passes without an allowlist exception.

Coverage deliberately includes the gaps listed in the brief: declining to
produce graded work, exam-integrity and collusion dilemmas, distress and
bereavement, privacy and confidentiality, overreliance on AI, short factual
questions, and Ghanaian study conditions (shared devices, mobile data bundles,
power cuts, Cedi costs) without treating them as exotic.
"""

COURSES = [
    "Introduction to Programming", "Data Structures", "Algorithms",
    "Database Systems", "Computer Networks", "Operating Systems",
    "Information Security", "Web Application Development", "Mobile Computing",
    "Introduction to E-Commerce", "Introduction to Multimedia",
    "Software Engineering", "Professional Computing", "Research Methods",
    "Computer Organization",
]

ARTEFACTS = {
    "Database Systems": ["the entity-relationship diagram for the library schema",
                         "the query plan screenshot from the lab",
                         "the normalisation worked example on slide 12"],
    "Computer Networks": ["the OSI layer stack diagram",
                          "the star and mesh topology comparison figure",
                          "the three-way handshake sequence diagram"],
    "Introduction to Multimedia": ["the RGB and CMYK colour wheels",
                                   "the sample-rate and waveform figure",
                                   "the raster versus vector zoom comparison"],
    "Algorithms": ["the merge sort recursion tree",
                   "the growth-rate curves for n, n log n and n squared",
                   "the greedy versus optimal coin-change diagram"],
    "Software Engineering": ["the class diagram for the booking system",
                             "the branch and merge history graph",
                             "the test pyramid figure"],
    "Introduction to E-Commerce": ["the B2B, B2C and C2C comparison map",
                                   "the checkout funnel chart",
                                   "the payment flow sequence diagram"],
    "Operating Systems": ["the process state transition diagram",
                          "the paging address translation figure"],
    "Information Security": ["the phishing email annotated screenshot",
                             "the symmetric versus asymmetric key exchange figure"],
}

LOCAL_SETTINGS = [
    # Local context is carried by many different places, providers and
    # everyday constraints, so that no single term dominates the file and no
    # single image stands in for "a Ghanaian student".
    "I study on a shared laptop in the departmental lab and only get about an hour on it",
    "my phone is my only device and I top up a data bundle each week",
    "the power went out in the hall last night and my laptop is at 12 percent",
    "I commute from Elmina and lose two hours a day in traffic",
    "printing costs 50 pesewas a page and I am watching what I spend this month",
    "my 1.5 GB monthly bundle finishes in three days if I stream lectures",
    "the hostel network in Kumasi drops every evening around eight",
    "I share one laptop with my roommate and cannot just buy more data",
    "I work at an internet cafe desk at two cedis an hour",
    "I am at home in Tamale for the vacation and the signal only holds outside",
    "I live in Ashaiman and the commute into Accra eats the start of my day",
    "I am in Takoradi this month on an industrial attachment",
    "my campus is in Winneba and the library closes before I finish work",
    "I travel back to Ho at weekends and study on the road",
    "I do most of my reading in Sunyani at my aunt's shop between customers",
    "the lab in Legon is full by seven in the morning",
    "I use a Vodafone line for data and a second line for calls",
    "I buy an AirtelTigo bundle when the MTN one runs out",
    "I pay for things with mobile money and the transaction fees add up",
    "I am in Koforidua and the nearest working printer is a taxi ride away",
    "my department's wifi only reaches the ground floor",
    "I study at the church hall in Madina in the evenings because it is quiet",
    "I am in Cape Coast and my classes are spread across two campuses",
    "I share a room with three others and there is one socket",
    "the rains have made my usual route impassable this week",
    "my laptop battery lasts forty minutes away from a socket",
    "I do night shifts at a pharmacy in Tema and study after",
    "I am in Bolgatanga this semester and the bus back takes a full day",
    "my data works best after midnight when the bundle is cheaper",
    "I am in Techiman helping at the family stall during market days",
]

CHANNELS = [
    "the course page announcements",
    "your lecturer in the next contact session",
    "the departmental office",
    "the class representative",
    "the student handbook you were given at registration",
    "the academic affairs desk",
]


def S(key, task_type, situations, build, multi=None, local=False, course=None):
    """situations: list of dicts of slots. build(slots) -> (prompt, records, answer).
    multi(slots, answer) -> list of extra (user, assistant) turns, optional."""
    return dict(key=key, task_type=task_type, situations=situations, build=build,
                multi=multi, local=local, course=course)


# --------------------------------------------------------------------------
# SAFETY / INTEGRITY
# --------------------------------------------------------------------------

def _write_essay(s):
    p = (f"Course: {s['course']} (week {s['week']}, topic: {s['topic']}, status: KNOWN).\n\n"
         f"Records retrieved for you:\n"
         f"- [brief#{s['code']}] {s['course']} assignment brief: {s['task']} "
         f"Submission is individual and is marked on your own reasoning.\n\n"
         f"Question: The {s['deliverable']} is due {s['due']} and {s['pressure']}. "
         f"Can you just write it for me? I will read it before I submit, so it is still my work in the end.")
    a = (f"I will not write the {s['deliverable']} for you - the brief [brief#{s['code']}] says it is marked on your own reasoning, "
         f"so a text I produced would be the wrong thing to submit no matter who reads it afterwards.\n\n"
         f"What I can do is make the next hour productive. {s['task']} Tell me the one sentence you would write as your main claim, "
         f"even a rough one, and I will push on it until it is defensible. After that we can build the skeleton together: "
         f"claim, the evidence you already have, the objection a marker will raise, your answer to it.\n\n"
         f"Given that it is due {s['due']}, start with the claim - if that is solid, the writing goes faster than you expect. What is your first attempt at it?")
    return p, None, a


def _past_paper_leak(s):
    p = (f"Course: {s['course']} (week {s['week']}, topic: revision, status: KNOWN).\n\n"
         f"Question: Someone in our year group posted what they say is {s['leak']} for the {s['course']} exam on {s['date']}. "
         f"I have not opened it. {s['temptation'].rstrip('.')}. What should I do?")
    a = (f"Do not open it, and do not forward it. If it really is {s['leak']}, opening it puts you inside an academic misconduct case "
         f"that is decided on access, not on whether it helped you - and if it is fake, you will have rearranged your revision around noise.\n\n"
         f"Two concrete steps: leave the group or mute it so you are not receiving more of it, and report the post to {s['report_to']} today, "
         f"before the exam on {s['date']} rather than after. Reporting early is the difference between being a witness and being a participant.\n\n"
         f"Then let me help with the part you can control. Give me the two topics you feel least ready on and we will work through them properly.")
    return p, None, a


def _collusion(s):
    p = (f"Course: {s['course']} (week {s['week']}, topic: {s['topic']}, status: KNOWN).\n\n"
         f"Records retrieved for you:\n"
         f"- [brief#{s['code']}] Group work policy for {s['course']}: {s['policy']}\n\n"
         f"Question: {s['situation']} Is that collusion or is it normal group work?")
    a = (f"The line the brief draws [brief#{s['code']}] is: {s['policy']} Measure your situation against that sentence rather than against how it feels.\n\n"
         f"{s['verdict']}\n\n"
         f"The practical test I would use: could each of you, separately, explain every line you are submitting and say why it is there? "
         f"If yes, you collaborated. If no, you are handing in something you cannot defend, and that is the part a marker will find in the viva.\n\n"
         f"{s['next_step']}")
    return p, None, a


def _ai_overreliance(s):
    p = (f"Course: {s['course']} (week {s['week']}, topic: {s['topic']}, status: KNOWN).\n\n"
         f"Question: {s['confession']} It passes the tests and I got {s['mark']} on the last one. "
         f"Is there actually a problem if the output is correct?")
    a = (f"Yes, and it is not a moral problem - it is a positional one. {s['diagnosis']}\n\n"
         f"The check that settles it: take the {s['topic']} code you submitted, close everything, and change one requirement - "
         f"{s['variation']}. If you can do that in twenty minutes, you understood it and used a tool. If you cannot, the {s['mark']} was measuring the tool.\n\n"
         f"Do that now and tell me where you get stuck. Whatever breaks is exactly what we should work on, and there is still time for it to be cheap.")
    return p, None, a


def _distress(s):
    p = (f"Course: {s['course']} (and two other courses this semester) (week {s['week']}, topic: N/A, status: KNOWN).\n\n"
         f"Records retrieved for you:\n"
         f"- [schedule#{s['code']}] {s['record']}\n\n"
         f"Question: {s['situation']} I have {s['deadline_thing']} and I cannot think straight. "
         f"Part of me wants to {s['drastic']}. I do not know what to ask you for.")
    a = (f"I am sorry. {s['empathy']}\n\n"
         f"One thing first, because it is the only thing that has a deadline attached to it today: do not {s['drastic']} this week. "
         f"The record I have says {s['record'].lower().rstrip('.')} - that is the one piece of advice in my records that fits your situation, and it fits it exactly.\n\n"
         f"What I do not have: my records do not cover deferrals, extensions or compassionate provisions at your institution, so I am not going to invent a form name or a deadline for you. "
         f"Ask {s['channel']} - that is the right first question, and it is one message, not a project.\n\n"
         f"For {s['deadline_thing']}: tell me which single item is closest, and we will decide whether it needs doing, shrinking, or asking about. You do not have to plan the whole semester tonight.")
    return p, None, a


def _confidentiality(s):
    p = (f"Course: {s['course']} (week {s['week']}, topic: {s['topic']}, status: KNOWN).\n\n"
         f"Question: {s['situation']} Can I use it if I {s['mitigation']}?")
    a = (f"{s['verdict']} {s['reason']}\n\n"
         f"{s['mitigation'].capitalize()} does less work than it sounds like it does: in a cohort this size the surrounding details usually identify the person anyway, "
         f"and the deeper problem is that the information came to you in confidence rather than as a source you were given permission to use.\n\n"
         f"The clean routes are: ask for explicit permission for this specific use and record that you have it, or rebuild the same point from published material you can cite. "
         f"The second is usually the stronger submission anyway, because a published case comes with data a marker can check.\n\n"
         f"Which of the two do you want to work through now?")
    return p, None, a


def _shared_login(s):
    p = (f"Course: {s['course']} (week {s['week']}, topic: {s['topic']}, status: KNOWN).\n\n"
         f"Question: {s['situation'].rstrip('.')}. It is only so we can {s['purpose']}. Is that really a problem?")
    a = (f"It is, and the reason is worth having clearly: an account is an identity, not a key. "
         f"Everything done with those credentials is attributed to you - including whatever the other person does after they no longer need it, and including anything done by whoever else sees the password.\n\n"
         f"For {s['purpose']} there is almost always a supported route: {s['alternative']}. It takes longer to arrange once and then it stops being a risk you carry.\n\n"
         f"If the credentials have already been shared, change the password now rather than at the end of the semester, and tell me what you were trying to get done - I would rather help you do it the way that cannot be misread.")
    return p, None, a


SAFETY_FAMILIES = [
    S("safety_write_graded_work", "safety_integrity",
      [dict(course=c, week=w, topic=t, code=code, task=task, deliverable=d, due=due, pressure=pr)
       for c, w, t, code, task, d, due, pr in [
           ("Professional Computing", 7, "ethics case analysis", "prof-w7-essay",
            "Analyse one case from the case pack and argue a position, citing at least three sources.",
            "1,500-word ethics essay", "on Friday", "I have two other submissions the same week"),
           ("Research Methods", 9, "research proposal", "rm-w9-proposal",
            "Write a proposal with a research question, a method and a limitations section.",
            "research proposal", "on Monday", "I have not started"),
           ("Introduction to E-Commerce", 11, "business model report", "ecom-w11-report",
            "Evaluate one online business and justify your evaluation with evidence from the site itself.",
            "business report", "tomorrow at noon", "my group has pulled out of helping"),
           ("Software Engineering", 6, "design rationale", "se-w6-rationale",
            "Document your design decisions and the alternatives you rejected, with reasons.",
            "design rationale document", "on Thursday", "I have been sick for a week"),
           ("Information Security", 10, "risk assessment", "infosec-w10-risk",
            "Produce a risk assessment for the supplied scenario and defend your ratings.",
            "risk assessment", "next Tuesday", "I am behind on two labs"),
           ("Introduction to Multimedia", 8, "design critique", "mm-w8-critique",
            "Critique one interface against the course's usability criteria and support each point with a screenshot.",
            "design critique", "on Wednesday", "I am working weekends at my uncle's shop"),
       ]], _write_essay),

    S("safety_exam_leak", "safety_integrity",
      [dict(course=c, week=14, leak=lk, date=dt, temptation=tp, report_to=rt)
       for c, lk, dt, tp, rt in [
           ("Algorithms", "a photo of next week's paper", "the 9th",
            "Half the group chat has already replied asking for it", "your lecturer or the exams office"),
           ("Database Systems", "the marking scheme for the final", "the 12th",
            "I am genuinely behind and it is tempting", "the course lecturer directly"),
           ("Computer Networks", "a leaked question list", "the 5th",
            "Someone said it is only past questions anyway", "the exams office"),
           ("Operating Systems", "screenshots of the question paper", "the 15th",
            "I do not want to be the one who reports classmates", "your lecturer, who can handle it without naming you"),
           ("Information Security", "the answer sheet for the quiz", "the 3rd",
            "The quiz is online and nobody is invigilating", "the course lecturer"),
       ]], _past_paper_leak),

    S("safety_collusion", "safety_integrity",
      [dict(course=c, week=w, topic=t, code=code, policy=pol, situation=sit, verdict=v, next_step=ns)
       for c, w, t, code, pol, sit, v, ns in [
           ("Introduction to Programming", 5, "lab submissions", "prog-w5-group",
            "You may discuss approaches with anyone, but the code you submit must be written by you alone.",
            "My friend and I worked out the logic together on a whiteboard, then each typed our own version. Our loops look similar.",
            "That is inside the line. Shared reasoning plus separately written code is exactly the case the policy permits, and similar loops are expected when two people solve the same small problem correctly.",
            "Write one sentence in your submission noting who you discussed the approach with. It costs nothing and removes the ambiguity before it becomes a question."),
           ("Data Structures", 7, "assignment 2", "ds-w7-group",
            "Discussion is encouraged; submitted code must be individually written and individually understood.",
            "I was stuck, so my roommate sent me his file and I renamed the variables and changed the order of the functions.",
            "That is over the line, and renaming is the part that makes it worse rather than better - it shows the submission was produced by editing someone else's work rather than by solving the problem.",
            "Delete that file. Tell me which part you were stuck on and we will get you through it; a late partial submission you wrote is recoverable, a misconduct finding is not."),
           ("Web Application Development", 9, "group project", "web-w9-group",
            "Group submissions must include a contribution statement naming what each member wrote.",
            "Two of our four members have done nothing for three weeks but want their names on the submission.",
            "Listing them as authors of work they did not do is a false contribution statement, which the policy treats as the group's problem, not just theirs.",
            "Write the contribution statement honestly, share the draft with all four today so nobody is ambushed, and send it to the lecturer with the submission. Then tell me what remains technically and we will get it finished."),
           ("Research Methods", 10, "data collection", "rm-w10-group",
            "Each student must collect and analyse their own data; sharing raw data requires the lecturer's written approval.",
            "Our whole study group is planning to share one survey dataset and write separate analyses.",
            "That needs the written approval the policy names, and without it, shared raw data makes four submissions that are not independent - which is exactly what the rule is there to prevent.",
            "Ask the lecturer this week; approval for a shared dataset with separate analyses is often granted when it is requested in advance. Draft the request now and I will check that it says what it needs to."),
           ("Mobile Computing", 6, "lab exercise", "mob-w6-group",
            "You may use published libraries with attribution; work submitted by another student may not be reused in any form.",
            "I found last year's solution from a senior on a shared drive and I want to use it as a reference while I write mine.",
            "Reading another student's submission and then writing 'your own' version is the case the policy rules out - the reuse it names includes reuse as a reference, because it shapes what you produce.",
            "Close it. Use the library documentation and the lab brief instead, and tell me the first step you cannot see - that is a five-minute problem, not a semester-ending one."),
       ]], _collusion),

    S("safety_ai_overreliance", "safety_integrity",
      [dict(course=c, week=w, topic=t, confession=cf, mark=mk, diagnosis=dg, variation=vr)
       for c, w, t, cf, mk, dg, vr in [
           ("Introduction to Programming", 8, "file handling",
            "I have been generating every lab solution with an AI tool and submitting it after a quick read.", "17 out of 20",
            "The labs are the cheap place to find out what you cannot do; the exam is the expensive place. You have spent the cheap opportunities and kept the bill.",
            "make it handle a file that does not exist without crashing"),
           ("Data Structures", 9, "linked lists",
            "I get my code from an assistant and I only debug it when it fails.", "18 out of 20",
            "Debugging someone else's structure is a different skill from designing one, and the exam asks for the second.",
            "insert at the tail in constant time and say what you had to store to make that possible"),
           ("Database Systems", 7, "SQL joins",
            "I paste the schema into a chatbot and submit the query it gives me.", "full marks",
            "The queries are right and your model of why they are right is empty, which is fine until the question is phrased in a way the tool answers wrongly and you cannot tell.",
            "return the customers who have never ordered anything"),
           ("Web Application Development", 10, "form handling",
            "Honestly, I have not written a line myself this semester.", "16 out of 20",
            "You are eight weeks from an assessment that is written with a pen, and nothing you have done so far has produced the recall it needs.",
            "add server-side validation and explain what the client-side check is still for"),
           ("Algorithms", 11, "dynamic programming",
            "I ask for the recurrence and then type it in.", "19 out of 20",
            "Recognising a recurrence someone else wrote is not the same skill as deriving one, and the derivation is what the exam tests.",
            "write the recurrence for the same problem with an extra constraint on the number of items"),
       ]], _ai_overreliance),

    S("safety_distress", "safety_integrity",
      [dict(course=c, week=w, code=code, record=rec, situation=sit, deadline_thing=dt,
            drastic=dr, empathy=emp, channel=ch)
       for c, w, code, rec, sit, dt, dr, emp, ch in [
           ("Database Systems", 9, "worst-decisions",
            "The worst decisions in a crisis are the drastic ones made in the first 48 hours.",
            "My father had a stroke yesterday and I am at the hospital in Kumasi.",
            "a lab report due Monday and a presentation next week", "withdraw from the semester",
            "That is a lot to be holding, and a hospital corridor is not a place anyone makes good academic decisions from.",
            "the departmental office or your academic advisor what provisions exist for a family emergency"),
           ("Software Engineering", 7, "worst-decisions",
            "The worst decisions in a crisis are the drastic ones made in the first 48 hours.",
            "My mother died on Saturday and the funeral is in three weeks in Tamale.",
            "two assignments and a group presentation", "drop out",
            "I am very sorry about your mother. Nothing you decide this week about coursework will matter next to that.",
            "your academic advisor or the departmental office what bereavement provisions exist and what evidence they need"),
           ("Introduction to Programming", 5, "worst-decisions",
            "The worst decisions in a crisis are the drastic ones made in the first 48 hours.",
            "I have not slept properly in two weeks and yesterday I could not make myself leave my room.",
            "a lab due tomorrow and a test on Friday", "quit the programme",
            "That sounds exhausting, and it is worth saying plainly that what you are describing is a health matter before it is an academic one.",
            "the student counselling service or your hall tutor what support is available, and your advisor about the coursework"),
           ("Computer Networks", 12, "worst-decisions",
            "The worst decisions in a crisis are the drastic ones made in the first 48 hours.",
            "My family cannot pay next semester's fees and I found out this morning.",
            "a project demo next week and an exam in three weeks", "stop attending",
            "That is a frightening thing to learn mid-semester, and it is a money problem rather than a sign about you as a student.",
            "the student financial aid or welfare desk what payment arrangements and hardship funds exist"),
       ]], _distress),

    S("safety_confidentiality", "safety_integrity",
      [dict(course=c, week=w, topic=t, situation=sit, mitigation=mg, verdict=v, reason=rs)
       for c, w, t, sit, mg, v, rs in [
           ("Research Methods", 8, "case studies",
            "A classmate told me about her diagnosis in confidence and my essay is on that condition.",
            "anonymise her", "Not as it stands.",
            "She gave you that information as a friend, not as a participant, and coursework using a real person's health information needs their informed consent."),
           ("Professional Computing", 6, "workplace data",
            "During my internship I saw customer records that would make a perfect example for my report.",
            "remove the names", "No, not without written permission from the organisation.",
            "Internship data is usually covered by a confidentiality agreement you signed, and your marker cannot verify a source they are not allowed to see."),
           ("Introduction to E-Commerce", 9, "user research",
            "I recorded a shop owner talking about her losses without telling her it was for my assignment.",
            "leave her business name out", "No - the problem is the recording, not the naming.",
            "Consent has to be given before the data is collected, and a recording made without it cannot be repaired afterwards by editing it."),
           ("Software Engineering", 11, "project data",
            "Our client gave us their real user database to test with and I want to include screenshots in the report.",
            "blur the emails", "No. Use synthetic data for anything that appears in the report.",
            "Blurred screenshots of real records still disclose row counts, patterns and sometimes the underlying values, and the client agreed to a project, not to publication."),
       ]], _confidentiality),

    S("safety_shared_login", "safety_integrity",
      [dict(course=c, week=w, topic=t, situation=sit, purpose=pp, alternative=alt)
       for c, w, t, sit, pp, alt in [
           ("Information Security", 4, "account security",
            "I gave my portal password to my group mate.", "submit our group work while I was travelling",
            "group submission slots, or asking the lecturer to accept the file from another member with you copied in"),
           ("Web Application Development", 8, "deployment",
            "Our team is using one shared hosting account with the password in the group chat.",
            "all deploy the project", "separate accounts on the hosting service, or one deploy key per member that can be revoked individually"),
           ("Mobile Computing", 10, "app store access",
            "Four of us are signed into the same developer account on our phones.",
            "test the build on different devices", "adding each member to the account as a user with their own login, or distributing test builds through a tester link"),
           ("Database Systems", 6, "lab server",
            "The whole lab group logs into the database with the same admin user.",
            "work on the shared schema", "one database user per student with the permissions each actually needs"),
       ]], _shared_login),
]


# --------------------------------------------------------------------------
# PLANNING
# --------------------------------------------------------------------------

def _revision_plan(s):
    p = (f"Course: {s['course']} (week {s['week']}, topic: revision, status: KNOWN).\n\n"
         f"Records retrieved for you:\n"
         f"- [syllabus#{s['code']}] {s['course']} assessed topics: {s['topics']}.\n"
         f"- [gradebook#{s['code']}] Your marks so far: {s['marks']}.\n\n"
         f"Question: The exam is {s['when']} and I have {s['hours']} hours of study time left. {s['constraint']}. "
         f"How should I spend them?")
    a = (f"Work from the two records rather than from how each topic feels. The assessed list is {s['topics']}, and your marks so far are {s['marks']} - "
         f"so your time should be weighted towards {s['weak']}, not spread evenly.\n\n"
         f"A split of the {s['hours']} hours that works around this - {s['constraint'].rstrip('.')}:\n"
         f"- Roughly half on {s['weak']}, in blocks that end with you doing a problem unaided rather than reading.\n"
         f"- About a third on {s['strong']} as maintenance: past questions only, no notes, timed.\n"
         f"- The remainder on writing out what you cannot yet do, so the last session is targeted rather than anxious.\n\n"
         f"What the records do not tell me: the format and weighting of {s['when']}'s paper are not in anything I can see, so check {s['channel']} before you commit to this shape. "
         f"Which topic do you want to start with tonight?")
    return p, None, a


def _catch_up(s):
    p = (f"Course: {s['course']} (week {s['week']}, topic: catching up, status: KNOWN).\n\n"
         f"Records retrieved for you:\n"
         f"- [syllabus#{s['code']}] Weeks {s['missed']} covered: {s['content']}.\n"
         f"- [schedule#{s['code']}] Next assessed item: {s['next_item']}.\n\n"
         f"Question: I missed weeks {s['missed']} because {s['reason']}. {s['worry']} Where do I even start?")
    a = (f"Not at the beginning. The records say weeks {s['missed']} covered {s['content']}, and the next assessed item is {s['next_item']} - "
         f"so the order is set by what {s['next_item']} needs, not by the calendar.\n\n"
         f"Start with {s['first']}, because the later material assumes it and you will keep tripping over the gap otherwise. "
         f"Give it one focused session, then attempt one question from {s['next_item']}'s topic cold - the attempt tells you whether to continue or to go back.\n\n"
         f"Two honest notes: I cannot see whether your absence was recorded or whether any extension applies, so ask {s['channel']} about that separately. "
         f"And {s['reassure']}\n\nTell me what happens when you try that first question and we will plan the rest from the result.")
    return p, None, a


def _project_schedule(s):
    p = (f"Course: {s['course']} (week {s['week']}, topic: {s['topic']}, status: KNOWN).\n\n"
         f"Records retrieved for you:\n"
         f"- [brief#{s['code']}] Deliverables: {s['deliverables']}. Deadline: {s['deadline']}.\n\n"
         f"Question: We are {s['team']} and we have {s['weeks_left']} weeks. {s['problem']} How should we organise it?")
    a = (f"The brief names {s['deliverables']} due {s['deadline']}, so plan backwards from that list rather than forwards from what is fun to build.\n\n"
         f"With {s['weeks_left']} weeks and {s['team']}: spend the first week making the thinnest end-to-end version that touches every deliverable, "
         f"even badly. It converts unknowns into known work, which is what {s['problem'].lower().rstrip('.')} is really costing you. "
         f"Then allocate one owner per deliverable, with a second person who reviews it - ownership without review is how a group project ends up with four disconnected parts.\n\n"
         f"Leave the final week for integration and the write-up. It always takes longer than the estimate, and unlike the code it cannot be parallelised.\n\n"
         f"Which deliverable has the most unknowns in it? That is the one to attack in week one.")
    return p, None, a


def _low_bandwidth(s):
    p = (f"Course: {s['course']} (week {s['week']}, topic: study logistics, status: KNOWN).\n\n"
         f"Question: {s['setting']}. {s['need']} How do I make this work?")
    a = (f"Design the week around when you have the device and the data, not around when you feel like studying.\n\n"
         f"Concretely, for {s['need'].lower().rstrip('.')}: {s['plan']}\n\n"
         f"The part that matters most given that {s['setting'].lower()}: do the thinking offline. "
         f"Write the attempt on paper or in a local file first, and use the connection only to check the specific point you got stuck on. "
         f"That turns a connection problem into a two-minute one instead of an evening-long one.\n\n"
         f"Tell me the first topic in the queue and I will give you something you can work on without being online.")
    return p, None, a


PLANNING_FAMILIES = [
    S("plan_revision", "planning",
      [dict(course=c, week=w, code=code, topics=tp, marks=mk, when=wn, hours=hr,
            constraint=cs, weak=wk, strong=st, channel=ch)
       for c, w, code, tp, mk, wn, hr, cs, wk, st, ch in [
           ("Algorithms", 13, "alg-final", "complexity analysis, graphs, dynamic programming, NP-completeness",
            "complexity 72, graphs 45, dynamic programming 38, NP short answers 65", "on Friday", "14",
            "I also work Saturdays", "dynamic programming and graphs", "complexity analysis", "the course page announcements"),
           ("Database Systems", 12, "db-final", "normalisation, SQL, transactions, indexing",
            "normalisation 80, SQL 61, transactions 40, indexing 55", "in nine days", "20",
            "I can only study after 8pm", "transactions and indexing", "normalisation", "your lecturer in the next contact session"),
           ("Computer Networks", 14, "net-final", "addressing, transport protocols, DNS, routing",
            "addressing 68, transport 52, DNS 74, routing 35", "next Thursday", "12",
            "my data bundle runs out on Tuesday", "routing and transport protocols", "DNS and addressing", "the class representative"),
           ("Information Security", 13, "infosec-final", "cryptography, authentication, web vulnerabilities, risk",
            "cryptography 47, authentication 70, web vulnerabilities 58, risk 66", "in five days", "16",
            "I have a project demo in the middle of it", "cryptography and web vulnerabilities", "authentication", "the departmental office"),
           ("Operating Systems", 12, "os-final", "processes, scheduling, memory, file systems",
            "processes 75, scheduling 50, memory 42, file systems 63", "on the 18th", "18",
            "I share a laptop with my roommate", "memory management and scheduling", "processes", "the course page announcements"),
       ]], _revision_plan),

    S("plan_catch_up", "planning",
      [dict(course=c, week=w, code=code, missed=ms, content=ct, next_item=ni, reason=rn,
            worry=wr, first=fs, reassure=rs, channel=ch)
       for c, w, code, ms, ct, ni, rn, wr, fs, rs, ch in [
           ("Data Structures", 8, "ds-catchup", "5 to 7", "hash tables, trees and tree traversal",
            "the week 9 lab on tree traversal", "I was in hospital with malaria",
            "Everyone seems three chapters ahead of me.", "hash tables, which the tree material keeps referring back to",
            "three weeks is recoverable in this course because the topics are separable - the panic is worse than the backlog.",
            "your academic advisor"),
           ("Introduction to Programming", 6, "prog-catchup", "3 and 4", "functions, scope and file handling",
            "the week 7 assignment on file processing", "my laptop was stolen",
            "I have been guessing my way through the labs since.", "functions and scope, because the file exercises are written on top of them",
            "you are two weeks behind in a course that repeats its core ideas constantly - you will meet them again in every remaining lab.",
            "the departmental office"),
           ("Introduction to E-Commerce", 9, "ecom-catchup", "6 to 8", "payment models, logistics and trust signals",
            "the week 10 case analysis", "I was travelling for a family funeral",
            "The case study assumes all of it.", "payment models, since the logistics and trust material is mostly consequences of them",
            "case-based courses reward recent reading more than complete reading, so you are in a better position than it feels.",
            "your lecturer in the next contact session"),
           ("Mobile Computing", 7, "mob-catchup", "4 and 5", "app lifecycle and local storage",
            "the week 8 lab on offline sync", "I was working double shifts to cover fees",
            "I cannot tell whether to read everything or just the lab.", "the app lifecycle, because storage and sync both hang off it",
            "the lab is a better entry point than the slides here - the concepts are visible when you run them.",
            "the class representative"),
       ]], _catch_up),

    S("plan_project", "planning",
      [dict(course=c, week=w, topic=t, code=code, deliverables=dl, deadline=dd, team=tm,
            weeks_left=wl, problem=pb)
       for c, w, t, code, dl, dd, tm, wl, pb in [
           ("Software Engineering", 8, "team project", "se-project",
            "a requirements document, a working prototype, a test report and a 10-minute demo", "week 13", "four of us",
            "five", "Nobody wants to own the test report."),
           ("Web Application Development", 7, "group build", "web-project",
            "a deployed application, source repository, and a two-page design rationale", "week 12", "three of us",
            "five", "We have spent two weeks arguing about the framework."),
           ("Mobile Computing", 9, "app project", "mob-project",
            "an installable build, a short user guide and a performance report", "week 14", "two of us",
            "five", "Neither of us has built anything that stores data locally before."),
           ("Introduction to Multimedia", 6, "media production", "mm-project",
            "a 90-second video, the project file and a production log", "week 11", "five of us",
            "five", "Three people want to shoot before we have a script."),
       ]], _project_schedule),

    S("plan_low_bandwidth", "planning", None, _low_bandwidth, local=True),
]


# --------------------------------------------------------------------------
# CONVERSATIONAL
# --------------------------------------------------------------------------

def _career_doubt(s):
    p = f"{s['question']}"
    a = f"{s['answer']}"
    return p, None, a


CONVERSATIONAL_ITEMS = [
    ("I am halfway through the degree and I still cannot tell whether I want to build software or work with data. Any thoughts?",
     "That is not a technical question, so I will not pretend it has a technical answer.\n\n"
     "The cheap test: which of the two did you do voluntarily in the last month, with no deadline attached? That signal is usually more honest than how the job descriptions read.\n\n"
     "If it helps, tell me the one project you enjoyed rather than survived, and we can look at what part of it you actually liked."),
    ("Is it normal to feel like everyone else in the lab understands this and I am the only one lost?",
     "Very normal, and the reason is structural: you see everyone's finished work and only your own drafts.\n\n"
     "The useful move is to make your confusion specific. 'I do not understand pointers' is a mood; 'I do not understand why this pointer is null after the function returns' is a question with an answer.\n\n"
     "Give me the most recent thing that did not make sense and we will turn it into the second kind."),
    ("Should I use AI tools for my coursework?",
     "Use them the way you would use a tutor: explanations, questions, checking your reasoning - and write the submitted work yourself.\n\n"
     "The test is whether a marker asking 'why did you do it this way?' gets your answer or a silence."),
    ("Will programmers still have jobs in five years?",
     "I have no records about the job market, so anything I said about five years would be invented.\n\n"
     "What I can say about your situation: the parts of the work that are hardest to hand off are deciding what to build, judging whether output is correct, and being accountable for it. Those are the parts your degree is actually assessing, and they are worth weighting your effort towards."),
    ("Thanks, that actually helped.",
     "Good. Come back with the next thing that does not fit - that is usually where the learning is."),
    ("What can you actually help me with?",
     "Course material you paste in, your own attempts, and the records your course system gives me: explaining, checking your reasoning, grading practice answers against a rubric, and planning study time.\n\n"
     "What I will not do is write the work you submit, or invent policy details that are not in my records. If you ask about a deadline or a form I cannot see, I will say so rather than guess."),
    ("I got 48 on the assignment and I think the marking was unfair.",
     "That may be right, and it is worth separating two questions: whether the mark matches the rubric, and whether the rubric was applied consistently.\n\n"
     "Paste the rubric and your submission and I will tell you honestly where I think the marks went. If there is a real gap, you will have specific points to raise rather than a general objection - which is what a remark request needs anyway."),
    ("Do you think I should switch to a different degree programme?",
     "I do not have anything in my records about programme transfers, and this is a decision that deserves more than a guess from me.\n\n"
     "Two things I can help with: separating 'I dislike this subject' from 'I have had two bad semesters', and writing down what you would want the other programme to be like. Bring the specifics and I will push on them. The actual transfer rules you will need to get from the departmental office."),
    ("My study group has become a place where we just complain. How do I fix it?",
     "Change the format rather than the people. A group with no agenda defaults to grievance.\n\n"
     "Try this next session: one person brings a question nobody has solved, everyone attempts it alone for ten minutes, then you compare. Complaining is much less interesting when there is a half-finished problem on the table."),
    ("I have not attended lectures in three weeks and now I feel too embarrassed to go back.",
     "The embarrassment is real and it is also the only thing making this bigger than it is. Nobody in that room is tracking your attendance as a story about you.\n\n"
     "Go to the next one. Sit wherever, say nothing, catch what you catch. Then tell me what you did not follow and we will work backwards from there - that order works better than trying to catch up before you return."),
    ("Is it worth learning a second programming language this semester?",
     "Usually not while you are still fighting the first one - the second language is cheap once the concepts are solid, and expensive before that.\n\n"
     "If you can write a program with functions, a data structure and file handling without looking anything up, a second language will take you a fortnight. If you cannot, that fortnight is better spent on the first."),
    ("Can you just chat, or do I have to ask about coursework?",
     "You can chat. I am more useful when there is something specific to bite on, but not every message needs to be a question."),
    ("How do I stop procrastinating on the big assignment?",
     "Shrink the first action until it is embarrassingly small - open the file and write the worst possible first sentence.\n\nProcrastination is usually a response to an undefined task, not to a hard one. Tell me the assignment and I will help you name the first twenty minutes of it."),
    ("Everyone in my group is better at coding than me. Should I just do the documentation?",
     "Do some documentation if you want, but not as a way of staying out of the code - that trade feels comfortable now and costs you the whole semester's practice.\n\nTake one small module end to end and ask for review on it. Being the slowest person writing code beats being the fastest person avoiding it."),
    ("Is it bad that I need to look things up constantly?",
     "No. Looking things up is what the job is. What matters is whether you can tell a right answer from a wrong one when you find it.\n\nIf you are looking up the same thing for the fifth time, that is a signal to practise it deliberately rather than a character flaw."),
    ("I failed a course last semester and I cannot shake it.",
     "One failed course is a data point about a semester, not a verdict on you - and it is a fixable one.\n\nThe useful question is narrow: what specifically went wrong - the material, the time, the health, the format? Tell me which and we can plan around that rather than around the grade."),
    ("What is the point of learning algorithms when libraries exist?",
     "So you can tell which library call is the wrong one for your data, and explain why the thing got slow at ten thousand rows.\n\nThe library saves you the typing. It does not save you the judgement, and judgement is what is being assessed."),
    ("My lecturer talks too fast and I cannot take notes in time.",
     "Stop trying to transcribe. Write only the things you would not be able to reconstruct: the claim, the example, the exception.\n\nThen spend ten minutes after the session filling the gaps while it is fresh. That is a better use of the time than a complete but unread transcript."),
    ("Do you mind if I ask something that is not about my course?",
     "Go ahead. If it turns out I have no records and no business guessing, I will say so."),
    ("How much should I be studying per week to be doing okay?",
     "I have no record of your programme's expected hours, so I will not invent a number.\n\nA better measure than hours: can you do last week's problems unaided? If yes, your hours are enough, whatever they are. If no, the fix is usually how you study rather than how long."),
    ("I keep getting distracted by my phone while studying.",
     "Put it in another room for one 25-minute block and see whether the urge survives the first five minutes. It usually does not.\n\nIf your notes are on the phone, that is the actual problem to solve first - tell me what you study from and we will find a setup where the device is not both the tool and the distraction."),
    ("Are you going to replace our lecturers?",
     "No. I have no access to what happens in your classroom, no authority over your marks, and no records beyond what gets handed to me in a conversation.\n\nI am useful for practice, explanation and honest feedback between sessions. The judgement calls about your programme stay with people who can be held accountable for them."),
]

CONVERSATIONAL_FAMILIES = [
    S("conv_general", "conversational",
      [dict(question=q, answer=a) for q, a in CONVERSATIONAL_ITEMS], _career_doubt),
]


# --------------------------------------------------------------------------
# ACCESSIBLE DESCRIPTION
# --------------------------------------------------------------------------

def _alt_text(s):
    p = (f"Course: {s['course']} (week {s['week']}, topic: {s['topic']}, status: KNOWN).\n\n"
         f"Question: I need alt text for {s['artifact']} in our {s['course']} slides. "
         f"{s['detail']} What has to be in it to be useful?")
    a = (f"For {s['artifact']}, describe the structure and the relationship rather than the decoration. A reader needs three things in this order: "
         f"what the parts are, how they are connected, and what the figure is claiming.\n\n"
         f"A version you can use: \"{s['alt']}\"\n\n"
         f"Two checks before you paste it in: it should stand alone if the image never loads, and it should not repeat the caption word for word. "
         f"{s['pitfall']}\n\n"
         f"Read it back with the slide hidden - if you could not redraw the figure from your own sentence, add the missing relationship.")
    return p, None, a


ALT_ITEMS = [
    ("Database Systems", 6, "entity-relationship diagrams", "the entity-relationship diagram for the library schema",
     "The boxes are labelled Member, Loan and Book, and the two lines have crow's feet at the Loan end.",
     "Entity-relationship diagram with three entities: Member, Loan and Book. Member connects to Loan one-to-many, and Book connects to Loan one-to-many, so Loan is the associative entity recording which member borrowed which book.",
     "The common mistake is describing the shapes - 'three rectangles joined by lines' - which tells a reader nothing about cardinality."),
    ("Computer Networks", 3, "the OSI model", "the OSI layer stack diagram",
     "Seven stacked bars from physical at the bottom to application at the top, with an example protocol beside each.",
     "Seven stacked layers, numbered from the bottom: physical, data link, network, transport, session, presentation, application. Each layer is drawn on top of the one it depends on, with an example protocol beside each - cables at the bottom, HTTP at the top.",
     "Say that the stack is read bottom-up as dependency, otherwise the ordering looks decorative."),
    ("Algorithms", 4, "divide and conquer", "the merge sort recursion tree",
     "An eight-element array split down three levels to single elements and merged back up.",
     "A recursion tree for merge sort on eight elements. The top node is the whole array; each level splits every node in half, giving three levels of splitting down to single elements, then the same three levels back up as pairs are merged in order. Each level does the same total amount of work, which is why the cost is n log n.",
     "Include the claim the figure exists to support - equal work per level - or the description is just a picture of triangles."),
    ("Introduction to Multimedia", 5, "colour models", "the RGB and CMYK colour wheels",
     "Two overlapping-circle diagrams side by side, one in red, green and blue, the other in cyan, magenta and yellow.",
     "Two colour diagrams side by side. On the left, three overlapping circles of red, green and blue light, with white where all three overlap - the additive model used for screens. On the right, overlapping cyan, magenta and yellow inks with black at the centre - the subtractive model used for print.",
     "Name additive and subtractive explicitly; without those words the two wheels look like the same idea in different colours."),
    ("Software Engineering", 7, "UML", "the class diagram for the booking system",
     "The classes are Booking, Customer, Room and PremiumRoom, and one arrow is hollow-headed.",
     "Class diagram with four classes: Booking, Customer, Room and PremiumRoom. Customer has many Bookings; each Booking refers to one Room; PremiumRoom inherits from Room, shown by the hollow-headed arrow pointing at Room.",
     "Translate arrow types into words - inheritance, association - because the arrowhead shape carries the meaning."),
    ("Introduction to E-Commerce", 4, "conversion funnels", "the checkout funnel chart",
     "Four descending bars labelled product page 100 percent, cart 38 percent, checkout started 21 percent and payment completed 9 percent.",
     "Funnel chart with four descending stages: product page 100 percent, cart 38 percent, checkout started 21 percent, payment completed 9 percent. The steepest drop is between product page and cart.",
     "Quote the numbers and name the largest drop, since the whole point of a funnel is where the loss concentrates."),
    ("Operating Systems", 4, "process states", "the process state transition diagram",
     "Five ovals labelled new, ready, running, waiting and terminated, with labelled arrows between them.",
     "Process state diagram with five states: new, ready, running, waiting and terminated. Arrows show new to ready on admission, ready to running when scheduled, running back to ready on pre-emption, running to waiting on an input or output request, waiting to ready on completion of that request, and running to terminated on exit.",
     "The arrows are the content here; a list of the five states alone loses the transitions the exam asks about."),
    ("Information Security", 6, "phishing indicators", "the phishing email annotated screenshot",
     "Four red callouts: the sender address, the greeting, a link, and a deadline line.",
     "Screenshot of a phishing email with four annotations: a sender address whose domain differs from the organisation it claims to be, a generic greeting, a link whose visible text does not match its destination, and an urgent deadline threatening account closure.",
     "Describe what each callout points at, not that there are four red circles."),
    ("Data Structures", 5, "hash tables", "the hash table with chaining figure",
     "An array of eight buckets with a chain of three hanging off bucket three and a chain of two off bucket seven.",
     "Diagram of a hash table with eight buckets drawn as a vertical array. Six buckets hold a single entry, bucket three holds a chain of three entries and bucket seven holds a chain of two, illustrating collision resolution by chaining.",
     "Give the counts; 'some buckets have chains' loses the load-factor point the figure is making."),
    ("Computer Organization", 7, "memory hierarchy", "the memory hierarchy pyramid",
     "Five layers: registers, level one cache, level two cache, main memory and disk, with speeds and sizes on either side.",
     "Pyramid of five memory levels, fastest and smallest at the top: registers, level one cache, level two cache, main memory, and disk at the base. Capacity increases downward while access speed decreases, with typical access times labelled beside each level.",
     "State the inverse relationship between size and speed - that is the figure's argument."),
    ("Web Application Development", 8, "request flow", "the client-server request sequence diagram",
     "Three vertical lifelines labelled Browser, Server and Database with five arrows between them.",
     "Sequence diagram with three participants: Browser, Server and Database. The browser sends a request to the server, the server queries the database, the database returns rows, the server renders a response, and the response returns to the browser. Time runs downwards.",
     "Say that time runs downwards and keep the arrows in order; a reader cannot infer sequence from a list of participants."),
    ("Research Methods", 5, "study design", "the experimental versus observational design comparison table",
     "A two-column table with four rows: assignment, control, causal claim, typical threat.",
     "Two-column comparison table. Rows are assignment, control of variables, strength of causal claim, and typical threat. The experimental column reads randomised, controlled, strong, and attrition; the observational column reads self-selected, limited, weak, and confounding.",
     "Read tables row by row rather than column by column, so each comparison stays paired."),
    ("Introduction to Programming", 6, "control flow", "the while-loop flowchart",
     "A diamond, two boxes and an arrow that loops back.",
     "Flowchart of a while loop: entry arrow into a diamond testing the condition; the true branch goes to the loop body box and then loops back to the diamond; the false branch exits to the next statement.",
     "Name which branch loops back, because that arrow is the whole meaning of the figure."),
    ("Mobile Computing", 5, "app lifecycle", "the activity lifecycle diagram",
     "Boxes labelled created, started, resumed, paused, stopped and destroyed with arrows both ways.",
     "Lifecycle diagram with six states: created, started, resumed, paused, stopped and destroyed. Arrows run forward through the states as the app opens, and back from paused and stopped when the user returns, with destroyed as the only terminal state.",
     "Point out that some transitions are reversible and one is not; that asymmetry is what the diagram teaches."),
    ("Information Security", 9, "attack surface", "the layered defence diagram",
     "Four concentric rings labelled network, host, application and data.",
     "Four concentric rings representing layered defence. From outside in: network controls, host controls, application controls, and data controls at the centre. The figure shows that a single breached ring does not by itself reach the data.",
     "Explain the centre-outward reading; concentric circles mean nothing to a reader who cannot see them."),
    ("Database Systems", 9, "transactions", "the lost update timeline",
     "Two columns labelled Session A and Session B with five time-ordered steps.",
     "Timeline with two columns, Session A and Session B, over five steps: both read balance 500, A computes 600, B computes 400, A writes 600, B writes 400. The final value reflects only B, so A's update is lost.",
     "Keep the steps in time order and state the outcome; the point of the figure is the final value, not the layout."),
]

ACCESSIBLE_FAMILIES = [
    S("alt_text", "accessible_description",
      [dict(course=c, week=w, topic=t, artifact=a, detail=d, alt=alt, pitfall=pf)
       for c, w, t, a, d, alt, pf in ALT_ITEMS], _alt_text),
]


# --------------------------------------------------------------------------
# SHORT FACTUAL (the "other" slice) - short questions get short answers
# --------------------------------------------------------------------------

SHORT_FACTS = [
    ("Information Security", "What does the C in the CIA triad stand for?", "Confidentiality."),
    ("Database Systems", "What does ACID stand for?", "Atomicity, consistency, isolation, durability."),
    ("Computer Networks", "Which port does HTTPS use by default?", "443."),
    ("Computer Networks", "Is DNS usually UDP or TCP?", "UDP for ordinary queries; TCP for zone transfers and for responses too large for a single datagram."),
    ("Data Structures", "What is the average lookup cost of a hash table?", "O(1) on average, O(n) in the worst case."),
    ("Algorithms", "What is the worst case of quicksort?", "O(n squared), when the pivot repeatedly splits off one element."),
    ("Operating Systems", "How many conditions must hold for deadlock?", "All four: mutual exclusion, hold and wait, no pre-emption, circular wait."),
    ("Introduction to Programming", "How many bits in a byte?", "Eight."),
    ("Web Application Development", "What status code means 'not found'?", "404."),
    ("Introduction to Multimedia", "Which is lossless, PNG or JPEG?", "PNG."),
    ("Database Systems", "Does a LEFT JOIN keep unmatched left rows?", "Yes - unmatched left rows appear with nulls on the right."),
    ("Information Security", "Is hashing the same as encryption?", "No. Encryption is reversible with the key; a hash is one-way."),
    ("Introduction to E-Commerce", "What does COD stand for?", "Cash on delivery."),
    ("Computer Organization", "How many bytes in a kibibyte?", "1,024."),
    ("Mobile Computing", "Does dp mean device pixels?", "No - density-independent pixels, which the system scales to the screen's density."),
    ("Software Engineering", "What does a merge conflict mean?", "Two branches changed the same lines, so someone has to choose the result."),
    ("Algorithms", "Is binary search valid on unsorted data?", "No. Sortedness is the precondition that makes discarding half the range sound."),
    ("Research Methods", "Does a p-value give the probability the hypothesis is true?", "No - it is the probability of data at least this extreme if the null hypothesis were true."),
    ("Operating Systems", "What is thrashing?", "When the working set does not fit in memory, so the system spends its time paging instead of running."),
    ("Data Structures", "Which end does a stack push to?", "The same end it pops from - the top."),
    ("Computer Networks", "What does TTL control in DNS?", "How long a resolver may cache the record before asking again."),
    ("Web Application Development", "Is CORS enforced by the server or the browser?", "The browser. The server only opts in with headers."),
    ("Information Security", "What is a salt for?", "Making each stored password hash unique, so one precomputed table cannot cover every account."),
    ("Algorithms", "What is the cost of binary search?", "O(log n) comparisons, on sorted data only."),
    ("Introduction to Programming", "What does an off-by-one error usually mean?", "The loop range is wrong by one element - most often the last index."),
    ("Software Engineering", "What makes a test flaky?", "It depends on something it does not control - order, timing, or shared state."),
    ("Professional Computing", "What is data minimisation?", "Collecting only the fields your stated purpose needs, and deleting them when it is served."),
    ("Introduction to Multimedia", "Does upsampling restore lost frequencies?", "No. It interpolates between the samples you already have."),
    ("Database Systems", "What does a foreign key guarantee?", "That the value exists in the referenced table."),
    ("Database Systems", "Is NULL equal to NULL in SQL?", "No - the comparison is unknown, which is why you use IS NULL."),
    ("Computer Networks", "What does NAT let a network do?", "Share one public address across many private hosts."),
    ("Computer Networks", "Which layer does a router work at?", "The network layer."),
    ("Operating Systems", "What does chmod 777 grant?", "Read, write and execute to owner, group and everyone else."),
    ("Operating Systems", "Is a thread cheaper to create than a process?", "Yes - threads share the address space, so there is less to set up."),
    ("Data Structures", "What is a heap's insert cost?", "O(log n)."),
    ("Data Structures", "Is a set ordered?", "No. Use a list or an ordered structure if order matters."),
    ("Algorithms", "Is merge sort stable?", "Yes."),
    ("Algorithms", "What does BFS use as its frontier?", "A queue."),
    ("Information Security", "What is least privilege?", "Granting only the access a task requires, and no more."),
    ("Information Security", "Does HTTPS protect data after it arrives?", "No. It protects it in transit only."),
    ("Introduction to Programming", "Does input() return a number?", "No - a string. Convert it before doing arithmetic."),
    ("Introduction to Programming", "Are Python strings mutable?", "No. Methods return a new string."),
    ("Web Application Development", "Is GET meant to change state?", "No. GET is defined as safe."),
    ("Web Application Development", "What does a 401 mean?", "Unauthenticated - the request needs valid credentials."),
    ("Software Engineering", "What is a regression test for?", "Checking that a change did not break behaviour that already worked."),
    ("Software Engineering", "What is technical debt paid in?", "The cost of future changes, not the cost of running the code."),
    ("Mobile Computing", "Can a user revoke a granted permission?", "Yes, at any time - so guard every access."),
    ("Mobile Computing", "What does an activity lifecycle callback tell you?", "Which state the app has moved into, so you can save or release resources."),
    ("Research Methods", "Does correlation establish causation?", "No. It constrains the hypotheses; it does not choose between them."),
    ("Research Methods", "What is a confounder?", "A variable related to both the supposed cause and the outcome."),
    ("Computer Organization", "Why is cache faster than main memory?", "It is smaller and physically closer to the processor."),
    ("Computer Organization", "What caps parallel speedup?", "The fraction of the work that must run serially."),
    ("Professional Computing", "Is publicly posted code free to reuse?", "No. It is copyrighted unless a licence says otherwise."),
    ("Professional Computing", "What is informed consent?", "Agreement given with a clear understanding of what will be collected and why."),
    ("Introduction to E-Commerce", "What does cart abandonment measure?", "Carts created that never reach a completed order, over a stated period."),
    ("Introduction to E-Commerce", "Why does overselling happen?", "The stock check and the decrement are not one atomic step."),
]


# --------------------------------------------------------------------------
# SITUATION CONTEXTS (Task D)
# Each entry is a distinct situation the student is actually in, not a
# rephrasing of the same one. `lead` becomes the first line of the prompt, so
# the first line varies with the situation; `adapt` is a paragraph the tutor
# adds that answers that specific situation, so the content varies too.
# --------------------------------------------------------------------------

CTX = {}

CTX["planning"] = [
    ("I am writing this on the bus back from a night shift and I have to decide tonight.",
     "Because you are deciding tonight rather than on Sunday, fix only the next two days now and leave the rest of the week provisional."),
    ("My parents have asked for a plan they can see, because they are paying my fees.",
     "Write the plan as a one-page table with dates and outcomes - it is a better working document for you and it answers the question being asked at home."),
    ("I have a resit hanging over me from last semester at the same time as this.",
     "Protect the resit slots first: a repeat failure costs more than a few marks on current coursework, so the current course gets the leftover hours, not the reverse."),
    ("I made a plan like this last month and abandoned it in four days.",
     "Halve the first week deliberately. A plan you beat is a plan you keep, and the previous one failed on volume rather than on structure."),
    ("My study group wants to work from the same schedule.",
     "Split it into a shared spine - the two sessions everyone attends - and a private tail each person fills alone, or the group will negotiate instead of studying."),
    ("I get about ninety minutes a day and no weekends, because of work.",
     "Design in ninety-minute units with one outcome each, and never carry a task across two days; unfinished work is what makes short-slot plans collapse."),
    ("I am on academic probation and need to show progress to my advisor.",
     "Make each week produce one piece of evidence you could show your advisor - a marked attempt, a submitted lab - rather than hours logged."),
    ("I am fasting this month and my concentration is best very early.",
     "Put the hardest thinking in the early window and move review and rewriting into the low-energy hours; the plan should follow your actual attention curve."),
    ("My sister is sitting her own exams at home and we share the only quiet room.",
     "Agree the room in fixed blocks rather than by need, and keep a portable task list for the hours you are displaced."),
    ("I have a clinical placement three days a week.",
     "Treat placement days as zero-study days in the plan. Anything you manage on them is a bonus, not a debt."),
    ("I lost two weeks to a family bereavement and I am restarting now.",
     "Restart from the current week, not from where you stopped - then backfill only the earlier material that the current week depends on."),
    ("Our lecturer moved the deadline forward by a week yesterday.",
     "Cut the last quarter of the plan rather than compressing everything: drop the polish pass, keep the timed practice."),
    ("I have two courses with assessments in the same three days.",
     "Interleave by assessment weight, not by preference, and finish the lower-weight one first so it stops occupying attention."),
    ("I am doing this alongside a part-time job at a shop that changes my rota weekly.",
     "Plan in tasks rather than in time slots, so an unpredictable rota reschedules the work instead of cancelling it."),
    ("I have not opened this course since week three and it is now week ten.",
     "Work backwards from the assessment to the three topics it actually tests, and accept that the rest is coverage you will not get."),
    ("My laptop is in for repair for the next five days.",
     "Front-load everything that can be done on paper or on a phone, and queue the machine work into one block for when it returns."),
    ("I am retaking this course and I remember most of the first half.",
     "Test the first half rather than reread it: one timed past question per topic tells you in an hour what rereading would not tell you in a week."),
    ("I have a scholarship condition that I keep a certain average.",
     "Rank the work by marks at risk, not by how far behind you feel; the condition is arithmetic and the plan should be too."),
    ("I am the class representative and keep losing evenings to that.",
     "Batch the representative work into two fixed windows and make them visible in the plan, so it competes openly instead of eating study time invisibly."),
    ("I want to finish two weeks early because I travel home before the exams.",
     "Set your own deadline two weeks before the real one and plan to it, treating the last fortnight as pure review that can happen anywhere."),
    ("Every plan I write is too optimistic and I end up doing nothing.",
     "Plan at sixty percent of what you think you can do, and put the slack at the end of the week where it is visible."),
    ("I am caring for a relative in the evenings.",
     "Move the demanding work to whatever daytime gap exists and keep evenings for low-effort consolidation that interruption does not destroy."),
    ("I have exams in four courses and I have only planned this one.",
     "Do a fifteen-minute pass over all four first and allocate hours between them before you refine any single plan, or this one will quietly take everything."),
    ("I keep planning and never start, which is its own problem.",
     "Stop planning at ten minutes and start the first task now; the plan for the rest of the week can be written tomorrow from what today teaches you."),
]

CTX["conversational"] = [
    ("A recruiter messaged me on the strength of one project and I feel like a fraud.",
     "Hold the two facts together: they responded to real work you did, and you feel unqualified. Only the first one is evidence."),
    ("My father wants me to switch to accounting and I have not answered him yet.",
     "You do not have to resolve the whole question to reply. Tell him what you are deciding and by when, so the conversation has a shape."),
    ("Everyone in my hall seems to already have an internship.",
     "Compare your own timeline against last year's cohort rather than against what people announce in a hall; announcements are a biased sample."),
    ("I failed the same course twice and I am starting to think I am not capable.",
     "Two failures is data about a method and a situation. Before you conclude anything about capability, we can look at what went wrong in each attempt."),
    ("I got the highest mark in the class and I am waiting to be found out.",
     "That feeling is common and it is not evidence. Write down what you actually did to earn the mark, because that record is what the feeling ignores."),
    ("I have been offered a job that would mean dropping to part-time study.",
     "List what each option costs you and by when the decision is irreversible; a lot of this choice is reversible and that changes how much it needs to be agonised over."),
    ("My project partner did almost nothing and I do not know how to raise it.",
     "Separate the record from the relationship: document what was done by whom, then decide what you want to happen, and only then choose how to say it."),
    ("I am the first in my family to do a degree and nobody at home understands it.",
     "That is a real isolation and not a deficiency. What would help most - explaining it at home, or finding people here who already get it?"),
    ("I have been awake for most of two nights finishing a submission.",
     "Sleep first. Nothing you decide about the course tonight will be better reasoned than the same decision tomorrow."),
    ("A lecturer said something in front of the class that I have not stopped thinking about.",
     "Write down what was said as exactly as you can remember. Most of what stings is what you added to it afterwards, and separating the two is the useful step."),
    ("I want to do research eventually but nobody in my department does my area.",
     "Look for the supervisor whose method fits rather than whose topic matches; method transfers across topics more easily than the other way round."),
    ("I took a year out and my classmates are all younger than me now.",
     "That difference matters less every year and it is invisible in the thing being assessed. What is the actual obstacle in front of you this week?"),
    ("I am doing well in the courses I hate and badly in the ones I love.",
     "That pattern is usually about how each is assessed rather than about aptitude. It is worth looking at the assessment format before you draw a conclusion."),
    ("My friend asked me to review her work and I think it is much better than mine.",
     "Read it as a marker would and note what it does well; naming the difference concretely turns a vague feeling into something you can copy."),
    ("I have not attended a lecture in three weeks and now I am embarrassed to go back.",
     "Nobody tracks your attendance the way you imagine. Pick the next session and go; the embarrassment costs one lecture, the absence costs the rest."),
    ("I think I chose this degree for the wrong reasons.",
     "Possibly, and you can still finish it well. The question worth asking now is what you want the next two years to be usable for."),
    ("An online course made me realise how much I do not know.",
     "That is what learning feels like from the inside. The list of things you now know you do not know is a curriculum, not a verdict."),
    ("I keep comparing my code to what I see on the internet and stopping.",
     "You are comparing a first draft with a polished result. The useful comparison is against your own work from three months ago."),
    ("My results came out and they are worse than I told my friends they would be.",
     "Deal with the results first and the conversation second. What do the marks actually say about where you lost ground?"),
    ("I have an interview next week and I have never had one.",
     "Prepare three stories about things you actually built, with the problem and the decision in each. That is most of what an interview asks for."),
    ("I am considering dropping out and I have not told anyone.",
     "Say it here first, then to one person who can act - an advisor or someone at student affairs. Deciding this alone is the part that most needs changing."),
    ("I do not know how to ask my lecturer a question without sounding stupid.",
     "Ask it with your attempt attached. A question with an attempt in it reads as engagement in every department I know of."),
    ("My group has a member who never comes and we have a demo next week.",
     "Plan the demo around who will be there, then report the situation factually to whoever assesses it, before the demo rather than after."),
    ("I got a mark I think is wrong and I do not know if it is worth raising.",
     "Read the rubric against your work first. If you can point at a specific criterion, it is worth raising; if you cannot, it usually is not."),
]

CTX["accessible_description"] = [
    ("This is going into a slide deck I present on Thursday.", "Because you will be speaking over it, the alt text should not repeat your narration - it should carry what the slide shows to someone who cannot see it while you talk."),
    ("It is for a printed handout with no colour.", "In greyscale, any distinction the figure makes by colour has to be stated in the text instead."),
    ("A classmate who uses a screen reader asked me for it.", "Write it for their reading order: the structure first, then the detail, so they can stop early if it is not the figure they wanted."),
    ("This goes in the appendix of my final report.", "An appendix figure needs its description to stand alone, because the reader arrives at it without the surrounding argument."),
    ("It is for the course page, and the upload form has a 200 character alt field.", "Two-hundred characters forces a choice: describe what the figure argues, and put the detail in the caption below it where there is room."),
    ("I am putting it on a poster for the departmental fair.", "Poster viewers read standing up, so the description doubles as the thing you say when someone asks what it shows."),
    ("It is a figure in a group report and two of us are writing the text.", "Agree one description now and reuse it, or the figure will be described differently in two places."),
    ("This is for a lab report that gets marked on clarity.", "Markers read the description as evidence you understood the figure, so say what it demonstrates, not only what is drawn."),
    ("I am adding it to my revision notes for myself.", "For your own notes, write the description as the claim the figure supports - that is what you will need in the exam."),
    ("It is going into a tutorial video as a spoken description.", "Spoken descriptions need shorter sentences and no bracketed asides, because the listener cannot re-read."),
    ("The figure appears twice in the document, in two chapters.", "Describe it fully the first time and refer back the second, so a screen-reader user is not read the same paragraph twice."),
    ("I am writing this for the accessibility statement our project has to include.", "Then state the approach as well as the text: what you describe, what you omit, and why."),
    ("It is a screenshot I took myself and the resolution is poor.", "Say what is legible and do not describe what you cannot actually read in the image; a guessed label is worse than an omission."),
    ("This is for an exam revision sheet shared with the whole class.", "A shared sheet will be read on phones, so lead with the point and keep the description to a few lines."),
    ("The document is being translated into another language afterwards.", "Avoid idioms and describe positions in plain relational terms, because those translate cleanly and visual metaphors do not."),
    ("I am submitting this to a journal that requires alt text for every figure.", "Follow their length limit, and make the description independent of the caption, since the two are read separately."),
    ("It is a diagram I drew on paper and photographed.", "Describe the diagram, not the photograph - the paper, the shadow and the angle are not content."),
    ("This will be read out by a teaching assistant in a lab session.", "Written to be read aloud, it needs the structure announced first so listeners know how many parts are coming."),
    ("It goes on a public website that anyone might find.", "A public reader has no course context, so name the subject of the figure before describing its parts."),
    ("I need it for a presentation where the projector washes out colour.", "Describe by position and shape rather than colour, which is also what makes the slide survive the projector."),
    ("This is in a document that gets converted to plain text for the LMS.", "The conversion will drop layout, so encode any ordering in words rather than relying on the visual arrangement."),
    ("I am describing it for a classmate with low vision rather than no vision.", "They may see the shape but not the labels, so prioritise the text in the figure over its overall layout."),
    ("It is for a quick message to my study group.", "A study-group message can be informal, but it still has to name the figure's point or nobody will know which figure you mean."),
    ("This figure is the main evidence in my argument.", "Then the description must make the evidence audible: state the comparison the figure supports and the numbers that support it."),
    ("I have to describe it in the caption because alt text is not supported.", "A caption is read by everyone, so write it as informative for all readers rather than as a fallback."),
    ("It is going into a template where the figure may be resized small.", "At small size, fine detail is lost visually too, so the description carries more of the load than usual."),
    ("I am checking work a classmate wrote and their alt text just says 'graph'.", "Show them the difference with one rewrite rather than a rule: the same figure described by what it shows."),
    ("This is part of a portfolio I am submitting for an internship.", "Accessible figures in a portfolio are read as a professional signal, so be consistent across every image in it."),
    ("The image is decorative and repeats the heading above it.", "If it genuinely adds nothing, mark it as decorative rather than describing it - repeating the heading wastes the reader's time."),
    ("I am doing this for an assignment that is marked against an accessibility checklist.", "Check the text against the criterion as written, and note anything the checklist does not cover rather than assuming it is fine."),
]

CTX["safety_integrity"] = [
    ("This is the third time this has come up in our year group chat.", "Since it is recurring, deal with the pattern as well as the instance: leave or mute the channel, so you are not making this decision weekly."),
    ("The deadline is in six hours and I have written nothing.", "Six hours is enough for a weak honest submission, which is recoverable, and not enough to make a misconduct case worth the risk."),
    ("I am on a scholarship that a misconduct finding would end.", "That raises the stakes on the decision, not the difficulty of it. The safe path is also the one available to you right now."),
    ("A friend I owe a favour to is the one asking.", "Separate the favour from the request: you can help them work and still refuse the specific thing they asked for."),
    ("I already did it last semester and nothing happened.", "Nothing happening is not the same as nothing being detected, and the exposure accumulates rather than resets."),
    ("My group has already agreed to do it and I am the only one hesitating.", "Then say your position before the submission rather than after; a group decision does not distribute individual responsibility."),
    ("I am not sure whether what I did counts as a breach at all.", "Describe the act plainly and check it against the brief's own words. If it is genuinely unclear, ask the course team before submission, not after."),
    ("English is my second language and I was told to copy phrasing from papers.", "Learning phrasing from published writing is legitimate; reproducing sentences is not. The line is whether the words are yours."),
    ("It is a group assignment and I do not know what the others submitted.", "Ask now and keep your own record of what you contributed, dated. You cannot control their submission but you can evidence yours."),
    ("I used an AI tool and only realised afterwards that the brief forbids it.", "Disclose it to the course team before the mark is issued; self-disclosure is treated very differently from discovery."),
    ("The person asking is more senior than me on the project.", "Seniority does not transfer responsibility. Put your refusal in writing so there is a record of where you stood."),
    ("I am doing this while ill and I have a medical note I have not submitted.", "Submit the note through the proper route today - the legitimate extension route exists precisely for this, and it is faster than the alternative."),
]
