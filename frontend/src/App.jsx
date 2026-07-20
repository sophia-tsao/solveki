import { useState, useEffect } from 'react';
import CourseList from './CourseList.jsx';
import MathProblem from './MathProblem.jsx';
import Header from './Header.jsx';
import Settings from './Settings.jsx';
import LoginPage from './LoginPage.jsx';
import { fetchMe } from './auth.js';

const PAGES = ["math", "courses", "settings"];

function pageFromHash() {
  const page = window.location.hash.replace(/^#\/?/, "");
  return PAGES.includes(page) ? page : "math";
}

function App() {
  const [currentPage, setCurrentPage]=useState(pageFromHash);
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  useEffect(() => {
    fetchMe()
      .then((data) => setUser(data.authenticated ? data.user : null))
      .catch(() => setUser(null))
      .finally(() => setAuthLoading(false));
  }, []);

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
    setUser(null);
    window.location.hash = "#/math";
    setCurrentPage("math");
  }

  if (authLoading) return null;

  if (!user) {
    return <LoginPage onLoggedIn={setUser} />;
  }

  return(
    <div>
      <Header currentPage={currentPage} linkClicked={(page)=>changeVisibility(page)}/>
      <div style={{paddingTop: '32px'}}>
        {currentPage==="math" && <MathProblem />}
        {currentPage==="courses" && <CourseList />}
        {currentPage==="settings" && <Settings onLoggedOut={handleLoggedOut} />}
      </div>
    </div>
  );
}

export default App;
