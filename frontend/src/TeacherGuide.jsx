import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './auth.js';
import './Teacher.css';

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
    <div className="teacher-page teacher-guide">
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
          A class is just a roster. Open <strong>Classes → New class</strong>, name it, and
          Solveki hands you a unique 6-character join code. Share the code; students enter it
          once to enroll. Open the class anytime to see who's joined or remove students.
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
              A good result grows the gap (1 day → 6 days → longer, up to a year); a poor one
              resets it to tomorrow.
            </p>
          </div>
        </div>

        <p style={{ marginTop: '1.25rem' }}>
          As a student practices, each topic climbs through four familiarity bands. Your
          progress graphs show the mix shifting toward the right over time:
        </p>
        <div className="tg-scale" aria-label="Proficiency bands by review interval">
          <span className="tg-scale-seg" style={{ background: '#ef4444' }}>New<small>seen daily</small></span>
          <span className="tg-scale-seg" style={{ background: '#f59e0b' }}>Learning<small>every few days</small></span>
          <span className="tg-scale-seg" style={{ background: '#3b82f6' }}>Familiar<small>a week or two</small></span>
          <span className="tg-scale-seg" style={{ background: '#22c55e' }}>Proficient<small>weeks+ apart</small></span>
        </div>
      </section>

      {/* 3. Assignments */}
      <section className="guide-section">
        <h2>3. Build an assignment</h2>
        <p>
          An assignment is a short set of topics you want a class to work on. You pick the
          topics and how many cards a day the deck should hold; Solveki adds those topics to
          each student's practice and grows their daily deck to that size.
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
              <strong>Set the number of cards</strong>
              <p>Choose how many cards a day the practice deck should hold while the assignment is active. SM-2 (section 2) picks which cards, so what's due surfaces first.</p>
            </div>
          </li>
          <li>
            <span className="guide-step-num">4</span>
            <div className="guide-step-body">
              <strong>Assign to classes &amp; set due dates</strong>
              <p>Check the classes that should get it and (optionally) a due date per class. Everyone enrolled receives it; the topics are added the first time each student opens it.</p>
            </div>
          </li>
        </ol>

        <div className="tg-flow" aria-label="What happens when a student opens an assignment">
          <span className="tg-pill">Student opens it</span>
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
            Your report shows how familiar they've grown with the assigned
            topics by the due date.
          </span>
        </div>
      </section>

      {/* 4. Progress */}
      <section className="guide-section">
        <h2>4. View progress</h2>
        <p>Progress drills down from the whole picture to a single student, three levels deep.</p>
        <div className="tg-flow" aria-label="How to drill into progress">
          <span className="tg-pill">Overview: all classes</span>
          <span className="tg-arrow">→</span>
          <span className="tg-pill">An assignment: familiarity by topic</span>
          <span className="tg-arrow">→</span>
          <span className="tg-pill">A student: topics &amp; history</span>
        </div>
        <ol className="guide-steps">
          <li>
            <span className="guide-step-num">1</span>
            <div className="guide-step-body">
              <strong>Overview</strong>
              <p>Your total student count plus a familiarity-over-time graph for all your students and one per class, so you can watch topics climb from New toward Proficient.</p>
            </div>
          </li>
          <li>
            <span className="guide-step-num">2</span>
            <div className="guide-step-body">
              <strong>Assignment results</strong>
              <p>Open any assignment to see how familiar the class has grown with its topics, and, per student, whether they've practiced by the due date and where each of the assigned topics sits.</p>
            </div>
          </li>
          <li>
            <span className="guide-step-num">3</span>
            <div className="guide-step-body">
              <strong>Student detail</strong>
              <p>Click a student to see their familiarity trend, per-topic mastery, and assignment history — the same view they see on their own dashboard.</p>
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
