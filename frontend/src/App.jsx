import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import CourseList from './CourseList.jsx';
import MathProblem from './MathProblem.jsx';
import Header from './Header.jsx';
import Settings from './Settings.jsx';
import Dashboard from './Dashboard.jsx';
import Diagnostic from './Diagnostic.jsx';
import LoginPage from './LoginPage.jsx';
import { fetchMe } from './auth.js';
import { createLogger } from './logger.js';
import './App.css';

const log = createLogger('app');

const PAGES = ["math", "dashboard", "courses", "settings", "diagnostic"];

function pageFromHash() {
  const page = window.location.hash.replace(/^#\/?/, "");
  return PAGES.includes(page) ? page : "math";
}

function App() {
  const queryClient = useQueryClient();
  const [currentPage, setCurrentPage]=useState(pageFromHash);

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

  const setSession = (nextUser) =>
    queryClient.setQueryData(['me'], nextUser
      ? { authenticated: true, user: nextUser }
      : { authenticated: false });

  useEffect(() => {
    const onHashChange = () => setCurrentPage(pageFromHash());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  // Keep the URL in sync with the page actually being shown. An empty or
  // unrecognized hash resolves to "math", so canonicalize it (e.g. a fresh
  // "solveki.vercel.app" becomes "solveki.vercel.app/#/math") once the user is
  // authenticated. Only runs while logged in, so it never fights the login
  // page's own hash handling.
  useEffect(() => {
    if (user && window.location.hash !== `#/${currentPage}`) {
      window.location.hash = `#/${currentPage}`;
    }
  }, [user, currentPage]);

  function changeVisibility(page){
    if(PAGES.includes(page)){
      window.location.hash = `#/${page}`;
      setCurrentPage(page);
    }
  }

  // Land first-time users on the Courses page so they pick a course before
  // practicing; returning users stay on whatever page the hash resolves to.
  function handleLoggedIn(data) {
    setSession(data.user);
    if (data.is_new_user) {
      changeVisibility("courses");
    }
  }

  function handleLoggedOut() {
    setSession(null);
    // Send the user to the landing page (the login page's own default view)
    // rather than a bare "#/math" that wouldn't match what's on screen.
    window.location.hash = "#/";
    setCurrentPage("math");
  }

  // The session check hits the backend (Cloud Run), which can cold-start for
  // several seconds. Show the same loading state as index.html rather than a
  // blank screen while we wait.
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

  return(
    <div className="app-shell">
      <Header currentPage={currentPage} linkClicked={(page)=>changeVisibility(page)}/>
      <main className="app-main">
        {currentPage==="math" && <MathProblem />}
        {currentPage==="dashboard" && <Dashboard />}
        {currentPage==="courses" && <CourseList userId={user.id} onStartDiagnostic={()=>changeVisibility("diagnostic")} />}
        {currentPage==="diagnostic" && <Diagnostic userId={user.id} onNavigate={(page)=>changeVisibility(page)} />}
        {currentPage==="settings" && <Settings onLoggedOut={handleLoggedOut} />}
      </main>
      <footer className="app-footer" />
    </div>
  );
}

export default App;
