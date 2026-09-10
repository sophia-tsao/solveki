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
          SM-2 is the scheduling algorithm behind Solveki's practice, and it's worth
          understanding before you build assignments. It schedules each <strong>topic</strong>
          {' '}(not individual problems), so a topic resurfaces right before a student is likely
          to forget it — frequent when shaky, rare once mastered.
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

        <p style={{ marginTop: '1.25rem' }}><strong>What's different when an assignment "counts toward SM-2":</strong></p>
        <div className="tg-flow">
          <span className="tg-pill">Student finishes</span>
          <span className="tg-arrow">→</span>
          <span className="tg-pill">1 grade per topic, from their accuracy</span>
          <span className="tg-arrow">→</span>
          <span className="tg-pill">Next review date shifts</span>
        </div>
        <div className="tg-branch">
          <span className="tg-branch-key tg-up">Higher accuracy ↑</span>
          <span>topic comes back <strong>later</strong> (longer gap)</span>
          <span className="tg-branch-key tg-down">Lower accuracy ↓</span>
          <span>topic comes back <strong>sooner</strong> (shorter gap)</span>
        </div>
        <div className="tg-scale" aria-label="Accuracy to review grade">
          <span className="tg-scale-seg" style={{ background: '#dc2626' }}>&lt;40%<small>grade 1</small></span>
          <span className="tg-scale-seg" style={{ background: '#f97316' }}>40–59%<small>grade 2</small></span>
          <span className="tg-scale-seg" style={{ background: '#eab308' }}>60–74%<small>grade 3</small></span>
          <span className="tg-scale-seg" style={{ background: '#84cc16' }}>75–89%<small>grade 4</small></span>
          <span className="tg-scale-seg" style={{ background: '#16a34a' }}>90–100%<small>grade 5</small></span>
        </div>
        <p className="tg-fine">
          Applied once per topic when the assignment is finished, and at most once per day per
          topic — shared with the student's normal daily practice, so an assignment can't grade
          the same topic twice in a day.
        </p>

        <div className="tg-note warn" style={{ marginTop: '0.75rem' }}>
          <span className="tg-note-icon">⚠</span>
          <span>
            With SM-2 <strong>off</strong>, an assignment is standalone practice: it's recorded
            for your analytics but never changes any topic's review schedule. Turn it on when the work should shape ongoing review.
          </span>
        </div>
      </section>

      {/* 3. Assignments */}
      <section className="guide-section">
        <h2>3. Build an assignment</h2>
        <p>Assignments come in two types. Pick the one that fits what you want students doing.</p>

        <div className="guide-compare">
          <div className="guide-box">
            <h4>Pick topics &amp; counts</h4>
            <p>
              You choose the topics and how many questions of each. Every student gets
              freshly generated problems on those same topics — same difficulty, different numbers.
              Best for a targeted worksheet.
            </p>
          </div>
          <div className="guide-box">
            <h4>Spaced-repetition deck</h4>
            <p>
              Pulls from each student's own practice topics, weighted by what's due for
              them today. You just set how many questions. Best for ongoing review that
              meets each student where they are.
            </p>
          </div>
        </div>

        <ol className="guide-steps">
          <li>
            <span className="guide-step-num">1</span>
            <div className="guide-step-body">
              <strong>Title it and pick a type</strong>
              <p>Give it a name and description, then choose "Pick topics" or "Deck".</p>
            </div>
          </li>
          <li>
            <span className="guide-step-num">2</span>
            <div className="guide-step-body">
              <strong>Choose content</strong>
              <p>For topics: check topics and set question counts. For a deck: choose whether it draws from all of the student's selected topics or a set you pick, and set the deck size.</p>
            </div>
          </li>
          <li>
            <span className="guide-step-num">3</span>
            <div className="guide-step-body">
              <strong>Decide whether it counts toward spaced repetition (SM-2)</strong>
              <p>A single checkbox — see section 2 above for exactly what changes when it's on.</p>
            </div>
          </li>
          <li>
            <span className="guide-step-num">4</span>
            <div className="guide-step-body">
              <strong>Assign to classes &amp; set due dates</strong>
              <p>Check the classes that should get it and (optionally) a due date per class. Everyone enrolled receives it; each student's problems are generated the first time they open it.</p>
            </div>
          </li>
        </ol>

        <div className="tg-note info">
          <span className="tg-note-icon">ℹ</span>
          <span>
            The two type choices and the SM-2 checkbox combine freely — so an assignment can be
            topics-with-SM-2, a plain deck, and so on.
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
          <span className="tg-pill">A class: roster &amp; accuracy</span>
          <span className="tg-arrow">→</span>
          <span className="tg-pill">A student: topics &amp; history</span>
        </div>
        <ol className="guide-steps">
          <li>
            <span className="guide-step-num">1</span>
            <div className="guide-step-body">
              <strong>Overview</strong>
              <p>Total students and overall accuracy, plus a card per class with size and completed-assignment counts.</p>
            </div>
          </li>
          <li>
            <span className="guide-step-num">2</span>
            <div className="guide-step-body">
              <strong>Assignment results</strong>
              <p>Open any assignment to see average accuracy, the topics students struggled with most, and each student's accuracy and time taken.</p>
            </div>
          </li>
          <li>
            <span className="guide-step-num">3</span>
            <div className="guide-step-body">
              <strong>Student detail</strong>
              <p>Click a student to see their per-topic mastery and full assignment history — the same view they see on their own dashboard.</p>
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
