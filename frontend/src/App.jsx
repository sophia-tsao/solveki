import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import CourseList from './CourseList.jsx';
import MathProblem from './MathProblem.jsx';
import Header from './Header.jsx';
import Settings from './Settings.jsx';
import Dashboard from './Dashboard.jsx';
import LoginPage from './LoginPage.jsx';
import { fetchMe } from './auth.js';
import { createLogger } from './logger.js';
import './App.css';

const log = createLogger('app');

const PAGES = ["math", "dashboard", "courses", "settings"];

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

  function changeVisibility(page){
    if(PAGES.includes(page)){
      window.location.hash = `#/${page}`;
      setCurrentPage(page);
    }
  }

  function handleLoggedOut() {
    setSession(null);
    window.location.hash = "#/math";
    setCurrentPage("math");
  }

  if (authLoading) return null;

  if (!user) {
    return <LoginPage onLoggedIn={setSession} />;
  }

  return(
    <div className="app-shell">
      <Header currentPage={currentPage} linkClicked={(page)=>changeVisibility(page)}/>
      <main className="app-main">
        {currentPage==="math" && <MathProblem />}
        {currentPage==="dashboard" && <Dashboard />}
        {currentPage==="courses" && <CourseList />}
        {currentPage==="settings" && <Settings onLoggedOut={handleLoggedOut} />}
      </main>
      <footer className="app-footer" />
    </div>
  );
}

export default App;
