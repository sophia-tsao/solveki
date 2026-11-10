import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './auth.js';
import { BANDS } from './BandBar.jsx';
import './Teacher.css';

// How often each band comes back for review, in BANDS order.
const SCALE_NOTES = ['seen daily', 'every few days', 'a week or two', 'weeks+ apart'];

// A visual "how it works" page for teachers. Brand-new teachers land here on
// first login (see App.handleRoleChosen); it stays reachable from the nav.
// Deliberately diagram-first — flows, steps and callouts instead of long prose —
// and reuses the tg-* guidance vocabulary from the assignment builder.
function TeacherGuide({ onGoToClasses, onGoToAssignments }) {
  // Only used to word the CTA: "Create your first class" vs "Create a new class".
  const classesQuery = useQuery({
    queryKey: ['classes'],
    queryFn: async () => {
      const res = await apiFetch('/classes/');
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
  });
  const hasClasses = (classesQuery.data?.classes?.length || 0) > 0;

  return (
    <div className="teacher-page teacher-page-narrow teacher-guide">
      <h1>How Solveki works for teachers</h1>
      <p className="guide-lede">
        You create classes, hand out assignments, and Solveki generates fresh
        problems for every student and tracks how they do. Here's the whole
        loop and what each piece does.
      </p>

      {/* The big picture, end to end. */}
      <div className="guide-bigflow" aria-label="The teaching loop, end to end">
        <span className="tg-pill">Create a class</span>
        <span className="tg-arrow">→</span>
        <span className="tg-pill">Students join with a code</span>
        <span className="tg-arrow">→</span>
        <span className="tg-pill">Build an assignment</span>
        <span className="tg-arrow">→</span>
        <span className="tg-pill">Assign to classes</span>
        <span className="tg-arrow">→</span>
        <span className="tg-pill">Students practice</span>
        <span className="tg-arrow">→</span>
        <span className="tg-pill">You watch progress</span>
      </div>

      {/* 1. Classes */}
      <section className="guide-section">
        <h2>1. Create a class</h2>
        <p>
          A class is just a roster. On <strong>Classes</strong>, type a name and choose
          {' '}<strong>Create class</strong>; Solveki hands you a unique 6-character join code
          (there's a Copy button on the class page). Share the code; students enter it once to
          enroll. The class page shows who's joined, and its <strong>Settings</strong> tab
          renames or archives the class.
        </p>
        <div className="tg-flow" aria-label="How students join a class">
          <span className="tg-pill">You create class</span>
          <span className="tg-arrow">→</span>
          <span className="tg-pill">Code: e.g. K7M2PQ</span>
          <span className="tg-arrow">→</span>
          <span className="tg-pill">Student enters code</span>
          <span className="tg-arrow">→</span>
          <span className="tg-pill">Enrolled</span>
        </div>
      </section>

      {/* 2. SM-2 */}
      <section className="guide-section">
        <h2>2. Why spaced repetition (SM-2)</h2>
        <p>
          SM-2 is the scheduling algorithm behind Solveki's practice — it runs automatically,
          with nothing to switch on. It schedules each <strong>topic</strong>
          {' '}(not individual problems), so a topic resurfaces right before a student is likely
          to forget it — frequent when shaky, rare once mastered. Every assignment simply adds
          topics to a student's practice, so the work they do on it feeds this same schedule.
        </p>

        <div className="guide-compare">
          <div className="guide-box">
            <h4>The benefit</h4>
            <p>
              Students spend time on what they're about to forget instead of re-drilling
              what they already know. Struggling topics come back fast; mastered ones stretch
              out to weeks or months, so review time keeps shrinking as they improve.
            </p>
          </div>
          <div className="guide-box">
            <h4>What it tracks per topic</h4>
            <p>
              An ease factor, an interval (days until next review), and a streak of successes.
              A good result on a due topic grows the gap (1 day → 3 days → 8 days → longer, up to a year); a poor one
              resets it to tomorrow.
            </p>
          </div>
        </div>

        <p style={{ marginTop: '1.25rem' }}>
          As a student practices, each topic climbs through four familiarity bands. Your
          progress graphs show the mix shifting toward the right over time:
        </p>
        <div className="tg-scale" aria-label="Proficiency bands by review interval">
          {BANDS.map((b, i) => (
            <span key={b.key} className="tg-scale-seg" style={{ background: b.color, color: b.ink }}>
              {b.label}<small>{SCALE_NOTES[i]}</small>
            </span>
          ))}
        </div>
      </section>

      {/* 3. Assignments */}
      <section className="guide-section">
        <h2>3. Build an assignment</h2>
        <p>
          An assignment is a short set of topics you want a class to work on. You pick the
          topics and how many cards students answer to finish it; Solveki adds those topics
          to each student's practice and stretches their deck so the cards fit.
        </p>

        <ol className="guide-steps">
          <li>
            <span className="guide-step-num">1</span>
            <div className="guide-step-body">
              <strong>Title it</strong>
              <p>Give it a name and an optional description so students know what it's for.</p>
            </div>
          </li>
          <li>
            <span className="guide-step-num">2</span>
            <div className="guide-step-body">
              <strong>Pick topics</strong>
              <p>Check the topics you want the class practicing. These are the topics the report tracks familiarity on.</p>
            </div>
          </li>
          <li>
            <span className="guide-step-num">3</span>
            <div className="guide-step-body">
              <strong>Set the minimum cards</strong>
              <p>Choose the fewest cards a student answers on the assigned topics. Solveki spreads them over the days until the due date. A student who gets them right finishes at that count; one who struggles gets more practice, up to 1.5 times as many, and is marked &ldquo;needs help&rdquo; if they reach that without getting solid. Cards on other topics don&rsquo;t count.</p>
            </div>
          </li>
          <li>
            <span className="guide-step-num">4</span>
            <div className="guide-step-body">
              <strong>Assign to classes &amp; set due dates</strong>
              <p>Check the classes that should get it and (optionally) a due date per class. Everyone enrolled receives it, and its topics are added to their decks right away. Students who join the class later get them when they join.</p>
            </div>
          </li>
        </ol>

        <div className="tg-flow" aria-label="What happens when you assign an assignment">
          <span className="tg-pill">You assign it</span>
          <span className="tg-arrow">→</span>
          <span className="tg-pill">Topics added to their deck</span>
          <span className="tg-arrow">→</span>
          <span className="tg-pill">They practice as normal</span>
          <span className="tg-arrow">→</span>
          <span className="tg-pill">SM-2 schedules the topics</span>
        </div>

        <div className="tg-note info">
          <span className="tg-note-icon">ℹ</span>
          <span>
            Your report shows where each student stands on the assigned topics
            right now, and flags anyone past the due date who hasn't finished
            their cards. To reuse an assignment, open its ⋯ menu on the
            Assignments page and choose Duplicate.
          </span>
        </div>
      </section>

      {/* 4. Progress */}
      <section className="guide-section">
        <h2>4. View progress</h2>
        <p>
          Progress drills down from what needs you today to a single student. Every page has
          breadcrumbs back up, and every table sorts by clicking a column header.
        </p>
        <div className="tg-flow" aria-label="How to drill into progress">
          <span className="tg-pill">Overview: what needs you</span>
          <span className="tg-arrow">→</span>
          <span className="tg-pill">A class or assignment</span>
          <span className="tg-arrow">→</span>
          <span className="tg-pill">A student: topics &amp; history</span>
        </div>
        <ol className="guide-steps">
          <li>
            <span className="guide-step-num">1</span>
            <div className="guide-step-body">
              <strong>Overview</strong>
              <p>
                This week in numbers: students on track for their weekly goal (three days&rsquo;
                worth of their daily cards), cards answered, first-try accuracy and overdue work,
                each compared with last week. <em>Needs attention</em> lists who is overdue or has
                gone quiet, who needs help, topics many students are missing (with a one-click
                follow-up assignment), and work due soon that students haven&rsquo;t started.
                Below are what&rsquo;s due this week, topics to revisit, and the familiarity
                trend. Switch it all to one class with the class picker.
              </p>
            </div>
          </li>
          <li>
            <span className="guide-step-num">2</span>
            <div className="guide-step-body">
              <strong>Class page</strong>
              <p>
                <em>Students</em> lists each student&rsquo;s familiarity, cards and accuracy this
                week, when they last practiced and any overdue work. <em>Progress</em> is a grid of
                every student against an assignment&rsquo;s topics: each cell shows their band
                (with its first letter), and a red ring marks a topic they missed lately. Tick
                {' '}<em>Hide names</em> before showing it on a projector.
              </p>
            </div>
          </li>
          <li>
            <span className="guide-step-num">3</span>
            <div className="guide-step-body">
              <strong>Assignment results</strong>
              <p>
                The counters across the top (Done, In progress, Not started, Overdue, Needs help)
                filter the student table; click one again to clear it. A student who
                hasn&rsquo;t answered a card yet counts as not started. Per student you&rsquo;ll
                see cards answered toward what they need, first-try accuracy, topics they&rsquo;re
                solid on, and their familiarity over time. The <em>Topics</em> tab shows what the
                class struggled with and the band mix per topic.
              </p>
            </div>
          </li>
          <li>
            <span className="guide-step-num">4</span>
            <div className="guide-step-body">
              <strong>Student detail</strong>
              <p>
                Alerts name the student&rsquo;s overdue work, their practice is compared with the
                class median, and their topics are listed weakest first with accuracy and next
                review. Step through the class with Prev / Next, or Print report for a parent
                conference.
              </p>
            </div>
          </li>
        </ol>
      </section>

      {/* Get started */}
      <div className="guide-cta">
        <p>Ready to set things up?</p>
        <button className="teacher-button" onClick={onGoToClasses}>{hasClasses ? 'Create a new class' : 'Create your first class'}</button>
        {' '}
        <button className="teacher-button secondary" onClick={onGoToAssignments}>Build an assignment</button>
      </div>
    </div>
  );
}

export default TeacherGuide;
