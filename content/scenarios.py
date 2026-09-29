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
    "I study on a shared laptop in the departmental lab in Cape Coast and only get about an hour on it",
    "my phone is my only device and I top up an MTN data bundle with mobile money every week",
    "dumsor took the power out in the hall last night and my laptop is at 12 percent",
    "I commute from Elmina and lose two hours a day in trotro traffic",
    "printing costs 50 pesewas a page and I am budgeting in cedis this month",
    "my 1.5 GB monthly bundle costs more than I want to spend and video lectures finish it in three days",
    "the hostel network in Kumasi drops every evening around eight",
    "I share one laptop with my roommate, and MoMo charges mean I cannot just buy more data",
    "I do my coursework on a shared desktop at an internet cafe at two cedis an hour",
    "I am at home in Tamale for the vacation and the signal only holds outside",
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
         f"A split of the {s['hours']} hours that fits {s['constraint']}:\n"
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
    a = (f"Describe the structure and the relationship, not the decoration. For {s['artifact']}, a reader needs three things in this order: "
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
]
