import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import CourseList from './CourseList.jsx';
import MathProblem from './MathProblem.jsx';
import Header from './Header.jsx';
import Settings from './Settings.jsx';
import Dashboard from './Dashboard.jsx';
import Diagnostic from './Diagnostic.jsx';
import LoginPage from './LoginPage.jsx';
import RolePicker from './RolePicker.jsx';
import Assignments from './Assignments.jsx';
import StudentClasses from './StudentClasses.jsx';
import TeacherOverview from './TeacherOverview.jsx';
import ClassList from './ClassList.jsx';
import ClassDetail from './ClassDetail.jsx';
import StudentDetail from './StudentDetail.jsx';
import TeacherAssignments from './TeacherAssignments.jsx';
import AssignmentBuilder from './AssignmentBuilder.jsx';
import AssignmentDetail from './AssignmentDetail.jsx';
import TeacherGuide from './TeacherGuide.jsx';
import { fetchMe } from './auth.js';
import { createLogger } from './logger.js';
import { parseHash, hashFor } from './router.js';
import './App.css';

const log = createLogger('app');

// Pages available per role. The hash router validates the requested page
// against the current user's set, so a student can't navigate to a teacher
// page by editing the URL (the backend also enforces this on every endpoint).
const STUDENT_PAGES = ["math", "dashboard", "courses", "settings", "diagnostic", "assignments", "student-classes"];
const TEACHER_PAGES = ["teacher-overview", "classes", "class-detail", "student-detail", "teacher-assignments", "assignment-builder", "assignment-detail", "teacher-guide", "settings"];

function pagesForRole(role) {
  return role === "teacher" ? TEACHER_PAGES : STUDENT_PAGES;
}

function routeForRole(role) {
  const route = parseHash();
  const pages = pagesForRole(role);
  if (pages.includes(route.page)) return route;
  return { page: role === "teacher" ? "teacher-overview" : "math", id: null, params: {} };
}

function App() {
  const queryClient = useQueryClient();

  // The session lives in the query cache under ['me']. Login and logout write
  // to it directly (setSession below) so every consumer sees the change without
  // a refetch. A network failure resolves to a logged-out session.
  const { data: session, isPending: authLoading } = useQuery({
    queryKey: ['me'],
    queryFn: async () => {
      try {
        const data = await fetchMe();
        log.info(data.authenticated ? 'Session restored' : 'No active session');
        return data;
      } catch (err) {
        log.error('Failed to check session:', err.message);
        return { authenticated: false };
      }
    },
  });
  const user = session?.authenticated ? session.user : null;
  const role = user?.role || "student";

  const [route, setRoute] = useState(() => routeForRole(role));

  // The first render runs before the session loads, so `role` is the "student"
  // fallback and a teacher's hash (e.g. "#/student-detail/5" on reload) gets
  // rejected. Re-resolve the hash once the real role is known — during render,
  // so the URL-sync effect below never sees (and writes back) the stale route.
  const [routeRole, setRouteRole] = useState(role);
  if (!authLoading && routeRole !== role) {
    setRouteRole(role);
    setRoute(routeForRole(role));
  }

  const setSession = (nextUser) =>
    queryClient.setQueryData(['me'], nextUser
      ? { authenticated: true, user: nextUser }
      : { authenticated: false });

  useEffect(() => {
    // Read the role fresh from the session cache rather than the closed-over
    // value: right after a role is chosen the closure is still stale, and a
    // hashchange fired by that navigation would otherwise bounce the new
    // teacher's "#/classes" back to the student default.
    const onHashChange = () => {
      const current = queryClient.getQueryData(['me']);
      const currentRole = current?.user?.role || "student";
      setRoute(routeForRole(currentRole));
    };
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, [queryClient]);

  // Keep the URL in sync with the page actually being shown once authenticated,
  // canonicalizing an empty/unknown hash to the role's default page.
  useEffect(() => {
    if (!user) return;
    const target = hashFor(route);
    if (window.location.hash !== target) {
      window.location.hash = target;
    }
  }, [user, route]);

  // `params` adds page context to the hash (e.g. { class: 3 }). `forRole`
  // overrides the current role for the page-validity check. It's needed right
  // after a role is chosen, when the ['me'] session update hasn't propagated
  // yet, so the closed-over `role` is still stale.
  function navigate(page, id = null, params = {}, forRole = role) {
    if (!pagesForRole(forRole).includes(page)) return;
    const next = { page, id, params: Object.fromEntries(
      Object.entries(params || {}).filter(([, v]) => v != null && v !== "").map(([k, v]) => [k, String(v)]),
    ) };
    window.location.hash = hashFor(next);
    setRoute(next);
  }

  // Land first-time students on Courses so they pick a course before practicing;
  // returning users stay on whatever page the hash resolves to. Role selection
  // (for brand-new users) is handled by the RolePicker gate below.
  function handleLoggedIn(data) {
    setSession(data.user);
    if (data.is_new_user && data.user.role_chosen && data.user.role === "student") {
      navigate("courses");
    }
  }

  function handleRoleChosen(chosenRole, chosenName) {
    // Refresh the session so user.role / role_chosen (and, for students who just
    // entered it, their name) reflect the choice, then route to the role's home.
    setSession({
      ...user,
      role: chosenRole,
      role_chosen: true,
      ...(chosenName ? { name: chosenName } : {}),
    });
    // Send brand-new teachers to the guide first so they see how classes,
    // assignments and SM-2 fit together before setting anything up.
    navigate(chosenRole === "teacher" ? "teacher-guide" : "courses", null, {}, chosenRole);
  }

  function handleLoggedOut() {
    setSession(null);
    window.location.hash = "#/";
    setRoute({ page: "math", id: null, params: {} });
  }

  if (authLoading) {
    return (
      <div className="app-boot">
        <div className="app-boot__spinner" aria-hidden="true" />
        <p className="app-boot__text">Loading…</p>
      </div>
    );
  }

  if (!user) {
    return <LoginPage onLoggedIn={handleLoggedIn} />;
  }

  // Brand-new users choose their role once before entering the app.
  if (!user.role_chosen) {
    return <RolePicker onChosen={handleRoleChosen} />;
  }

  const { page, id, params = {} } = route;
  const paramId = (key) => (params[key] && /^\d+$/.test(params[key]) ? Number(params[key]) : null);
  return (
    <div className="app-shell">
      <Header currentPage={page} role={role} linkClicked={(p) => navigate(p)} />
      <main className="app-main">
        {/* Student pages */}
        {page === "math" && (
          // Keyed by the assignment so switching decks starts from a clean card.
          <MathProblem
            key={id ?? "practice"}
            assignmentId={id}
            onOpenAssignment={(aid) => navigate("math", aid)}
            onExit={() => navigate("assignments")}
          />
        )}
        {page === "dashboard" && <Dashboard />}
        {page === "courses" && <CourseList userId={user.id} onStartDiagnostic={() => navigate("diagnostic")} />}
        {page === "diagnostic" && <Diagnostic userId={user.id} onNavigate={(p) => navigate(p)} />}
        {page === "assignments" && <Assignments onStarted={(aid) => navigate("math", aid)} />}
        {page === "student-classes" && <StudentClasses />}
        {/* Teacher pages */}
        {page === "teacher-overview" && (
          <TeacherOverview
            userName={user.name}
            onOpenClasses={() => navigate("classes")}
            onOpenStudent={(sid, cid) => navigate("student-detail", sid, { class: cid })}
            onOpenAssignment={(aid, p = {}) => navigate("assignment-detail", aid, p)}
            onCreateAssignment={() => navigate("assignment-builder")}
            onFollowUp={(tid, cid) => navigate("assignment-builder", null, { topic: tid, class: cid })}
          />
        )}
        {page === "classes" && <ClassList onOpenClass={(cid) => navigate("class-detail", cid)} />}
        {page === "class-detail" && (
          <ClassDetail
            key={id}
            classId={id}
            tab={params.tab}
            onTabChange={(tab) => navigate("class-detail", id, { tab })}
            onBack={() => navigate("classes")}
            onOpenStudent={(sid) => navigate("student-detail", sid, { class: id })}
            onOpenAssignment={(aid) => navigate("assignment-detail", aid, { class: id })}
          />
        )}
        {page === "student-detail" && (
          <StudentDetail
            key={id}
            studentId={id}
            classId={paramId("class")}
            onOpenClasses={() => navigate("classes")}
            onOpenClass={(cid) => navigate("class-detail", cid)}
            onOpenStudent={(sid, cid) => navigate("student-detail", sid, { class: cid })}
            onOpenAssignment={(aid) => navigate("assignment-detail", aid)}
          />
        )}
        {page === "teacher-assignments" && (
          <TeacherAssignments
            onCreate={() => navigate("assignment-builder")}
            onOpen={(aid) => navigate("assignment-detail", aid)}
            onEdit={(aid) => navigate("assignment-builder", aid)}
          />
        )}
        {page === "assignment-builder" && (
          <AssignmentBuilder
            key={`${id}-${params.topic || ""}-${params.class || ""}`}
            assignmentId={id}
            initialTopicId={paramId("topic")}
            initialClassId={paramId("class")}
            onDone={() => navigate("teacher-assignments")}
          />
        )}
        {page === "assignment-detail" && (
          <AssignmentDetail
            key={id}
            assignmentId={id}
            initialClass={paramId("class")}
            initialStatus={params.status}
            onOpenStudent={(sid, cid) => navigate("student-detail", sid, { class: cid })}
            onEdit={() => navigate("assignment-builder", id)}
            onBack={() => navigate("teacher-assignments")}
          />
        )}
        {page === "teacher-guide" && <TeacherGuide onGoToClasses={() => navigate("classes")} onGoToAssignments={() => navigate("teacher-assignments")} />}
        {/* Shared */}
        {page === "settings" && <Settings onLoggedOut={handleLoggedOut} />}
      </main>
    </div>
  );
}

export default App;
