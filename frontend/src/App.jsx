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
import AssignmentPlayer from './AssignmentPlayer.jsx';
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
import './App.css';

const log = createLogger('app');

// Pages available per role. The hash router validates the requested page
// against the current user's set, so a student can't navigate to a teacher
// page by editing the URL (the backend also enforces this on every endpoint).
const STUDENT_PAGES = ["math", "dashboard", "courses", "settings", "diagnostic", "assignments", "assignment-play", "student-classes"];
const TEACHER_PAGES = ["teacher-overview", "classes", "class-detail", "student-detail", "teacher-assignments", "assignment-builder", "assignment-detail", "teacher-guide", "settings"];

function pagesForRole(role) {
  return role === "teacher" ? TEACHER_PAGES : STUDENT_PAGES;
}

// Parse "#/page" or "#/page/42" into { page, id }. The optional id backs the
// detail pages (class/assignment/student) without pulling in a router library.
function parseHash() {
  const raw = window.location.hash.replace(/^#\/?/, "");
  const [page, idStr] = raw.split("/");
  const id = idStr && /^\d+$/.test(idStr) ? Number(idStr) : null;
  return { page, id };
}

function routeForRole(role) {
  const { page, id } = parseHash();
  const pages = pagesForRole(role);
  if (pages.includes(page)) return { page, id };
  return { page: role === "teacher" ? "teacher-overview" : "math", id: null };
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
    const target = route.id != null ? `#/${route.page}/${route.id}` : `#/${route.page}`;
    if (window.location.hash !== target) {
      window.location.hash = target;
    }
  }, [user, route]);

  // `forRole` overrides the current role for the page-validity check. It's needed
  // right after a role is chosen, when the ['me'] session update hasn't propagated
  // yet, so the closed-over `role` is still stale.
  function navigate(page, id = null, forRole = role) {
    if (!pagesForRole(forRole).includes(page)) return;
    window.location.hash = id != null ? `#/${page}/${id}` : `#/${page}`;
    setRoute({ page, id });
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
    navigate(chosenRole === "teacher" ? "teacher-guide" : "courses", null, chosenRole);
  }

  function handleLoggedOut() {
    setSession(null);
    window.location.hash = "#/";
    setRoute({ page: "math", id: null });
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

  const { page, id } = route;
  return (
    <div className="app-shell">
      <Header currentPage={page} role={role} linkClicked={(p) => navigate(p)} />
      <main className="app-main">
        {/* Student pages */}
        {page === "math" && <MathProblem />}
        {page === "dashboard" && <Dashboard />}
        {page === "courses" && <CourseList userId={user.id} onStartDiagnostic={() => navigate("diagnostic")} />}
        {page === "diagnostic" && <Diagnostic userId={user.id} onNavigate={(p) => navigate(p)} />}
        {page === "assignments" && <Assignments onOpen={(assignmentId) => navigate("assignment-play", assignmentId)} />}
        {page === "assignment-play" && <AssignmentPlayer assignmentId={id} onDone={() => navigate("assignments")} />}
        {page === "student-classes" && <StudentClasses />}
        {/* Teacher pages */}
        {page === "teacher-overview" && <TeacherOverview onOpenClass={(cid) => navigate("class-detail", cid)} />}
        {page === "classes" && <ClassList onOpenClass={(cid) => navigate("class-detail", cid)} />}
        {page === "class-detail" && <ClassDetail classId={id} onBack={() => navigate("classes")} onOpenStudent={(sid) => navigate("student-detail", sid)} />}
        {page === "student-detail" && <StudentDetail studentId={id} />}
        {page === "teacher-assignments" && (
          <TeacherAssignments
            onCreate={() => navigate("assignment-builder")}
            onOpen={(aid) => navigate("assignment-detail", aid)}
            onEdit={(aid) => navigate("assignment-builder", aid)}
          />
        )}
        {page === "assignment-builder" && <AssignmentBuilder assignmentId={id} onDone={() => navigate("teacher-assignments")} />}
        {page === "assignment-detail" && <AssignmentDetail assignmentId={id} onOpenStudent={(sid) => navigate("student-detail", sid)} onBack={() => navigate("teacher-assignments")} />}
        {page === "teacher-guide" && <TeacherGuide onGoToClasses={() => navigate("classes")} onGoToAssignments={() => navigate("teacher-assignments")} />}
        {/* Shared */}
        {page === "settings" && <Settings onLoggedOut={handleLoggedOut} />}
      </main>
      <footer className="app-footer" />
    </div>
  );
}

export default App;
