# Solveki demo script (~7 minutes)

## Before you start

- **Two Google accounts, two browser windows.** The role is set once at sign-up and can't be changed, so you need one student account and one teacher account. Use a normal window for the student and an incognito window (or a second profile) for the teacher.
- **Student account:** has already signed up and picked "I'm a student", so the role picker doesn't appear. If you want the Dashboard to look full, seed some practice history for this account ahead of time.
- **Teacher account:** set up ahead of time:
  - a class (write down its 6-character join code);
  - one assignment for that class, with a small card count (say 5) and a due date;
  - a few students with practice history already in the class, so the Overview chart and results table have data. That practice needs to happen after commit d667928. Answers from before it weren't logged, so the Struggled with most list, time and accuracy would show as empty.
- **Student not yet in the class.** That way you can join it live in step 6.
- **Know a few answers.** Pick a topic where you can answer correctly at a glance. Plan to miss one card on purpose to show the feedback.
- **Practice deck size set to 10** (the default) for the student, so you can change it during step 4.

---

## 1. Google login (~30s)

**Do:** Open the landing page.

**Say:** "This is Solveki. It's free math practice for grades 1–12 and AP, built on spaced repetition. It shows you each topic again just before you'd forget it."

**Do:** Click **Log in / Register**, then **Continue with Google**, and choose the test student account.

**Say:** "Sign-in is Google only, so there are no passwords to manage. The first time you sign in, you choose student or teacher. This account has already done that, so it goes straight in."

## 2. Available Courses (~45s)

**Do:** Click **Available Courses** in the nav.

**Say:** "Students choose what to review. There are 324 topics, from counting up to AP calculus."

**Do:**
- Type a topic into **Search courses and topics…**.
- Expand a course to show its topics grouped by unit.
- Tick one topic, then tick a whole course.

**Say:** "Ticking a course selects every topic in it. Changes save as soon as you click."

## 3. Diagnostic (~1 min)

**Do:** Click **Take the 5-question diagnostic**.

**Say:** "Students who don't know where to start can let Solveki choose for them."

**Do:**
- Q1: pick a course.
- Q2: pick the unit the student is on now, then click **Start problems**.
- Answer the three problems.

**Say:** "There are two questions about what you're studying, then three problems from units you've already covered. Solveki uses the results to decide which topics are new to you and which you already know."

**Do:** On **You're all set!**, point at the topic count, then click **Start practicing**.

## 4. Practice, then deck size in Settings (~1.5 min)

**Do:** Point at the card header: **1 of 10 questions**, **Attempt 1 of 2**, and the topic name.

**Say:** "Practice is a deck of cards. The problems are generated fresh each time, so students can't memorize answers. Topics that are due show up first."

**Do:** Answer one card correctly. It flips to a green check and moves on by itself.

**Do:** Answer the next card wrong twice. Point at **The answer is …** and the **Learn more ↗** link.

**Say:** "You get two tries. If you still miss it, you see the answer and a link to a video lesson, usually from Khan Academy. Solveki schedules the topic based on how you did. Right the first time means a longer gap before you see it again; a miss means you see it again tomorrow."

**Do:** Click **Continue**. Open **Settings**, change **Questions per practice** from 10 to 15, and click **Save**.

**Do:** Go back to **Practice**. The header now reads **… of 15 questions**.

**Say:** "Students choose how many cards they do each day, and the change applies right away. A new deck starts every day at midnight, local time."

## 5. Dashboard (~45s)

**Do:** Click **Dashboard**.

**Say:**
- "The donut shows every selected topic in one of four bands: **New**, **Learning**, **Familiar** and **Proficient**. The bands are based on how long the gap between reviews has become."
- "The calendar shows the days the student practiced."
- "Below that are the topics in each band, plus **Shown soon**, which is what the next session will draw from."

## 6. Classes (~30s)

**Do:** Click **Classes**, enter the teacher's join code, and click **Join**. Point at **Joined "…"** and the class under **My classes**.

**Say:** "A teacher gives out a six-letter code and students type it in. That's the only setup."

## 7. Assignments (~45s)

**Do:** Click **Assignments**.

**Say:** "Joining the class picked up the teacher's assignment straight away. Its topics have already been added to my practice."

**Do:** Point at the row: class, **Due …**, **0/5 cards**. Click **Practice**.

**Say:** "Assignments don't need a separate worksheet. Every card I answer in normal practice counts toward the assignment. When I reach the card count, it moves to **Done**."

**Do:** Answer a card or two, go back to **Assignments**, and show that the count has gone up.

## 8. Teacher view (~1.5 min)

**Do:** Switch to the teacher window. It opens on **Overview**.

**Say:** "This is the same app, signed in as a teacher. The chart shows the share of all students' topics in each band over the last 90 days."

**Do:** Choose the demo class in **Show familiarity for**. Then click the demo class's card below the chart to open the class page.

**Say:** "This is the class page. Each student has a familiarity bar, so you can see at a glance who's still mostly red and who's mostly green."

**Do:** Click **Assignments**, then **Results** on the demo assignment.

**Say:**
- "This is the assignment report. It shows how many students have finished and the band mix on the assigned topics."
- "**Struggled with most** lists the assigned topics with the lowest first-try accuracy, and how many students missed each one. That tells you what to reteach tomorrow."
- "**Familiarity by topic** breaks that down topic by topic. Below it is a row for each student with cards done, due date and overdue flags."
- "The test student we just used is in the list, and the cards they answered are already counted."

**Do:** Click the test student's name.

**Say:**
- "This page shows one student. Under **Practice** you can see how consistently they've practiced over the last four weeks, their current streak, and for the last seven days, how many questions they answered, how long they spent and how often they got it right on the first try."
- "Below that are the topics they've struggled with most this month, their assignments, and the same topic breakdown they see on their own dashboard."

**Do (optional, ~20s):** Go back to **Assignments**, click **New assignment**, and scroll through it without saving: topic picker, **Number of cards**, **Assign to classes** with due dates.

**Say:** "Making an assignment takes three steps: choose topics, set a card count, and choose classes. Once it's assigned, every student starts on it automatically."

## Close (~15s)

**Say:** "Solveki gives students endless practice that adapts to them, and gives teachers a live view of who's keeping up and what they're stuck on. And it's free."

---

## Things to avoid saying

- That users can switch between student and teacher. They can't.
- That the diagnostic adapts to answers during the test. Its three problems are fixed in advance; only the topics it picks afterwards depend on the results.
