import { useState, useEffect } from 'react';
import CourseList from './CourseList.jsx';
import MathProblem from './MathProblem.jsx';
import Header from './Header.jsx';
import Settings from './Settings.jsx';
import LoginPage from './LoginPage.jsx';
import { fetchMe } from './auth.js';

function App() {
  const [currentPage, setCurrentPage]=useState("math");
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  useEffect(() => {
    fetchMe()
      .then((data) => setUser(data.authenticated ? data.user : null))
      .catch(() => setUser(null))
      .finally(() => setAuthLoading(false));
  }, []);

  function changeVisibility(page){
    if(page==="math" || page==="courses" || page==="settings"){
      setCurrentPage(page);
    }
  }

  function handleLoggedOut() {
    setUser(null);
    setCurrentPage("math");
  }

  if (authLoading) return null;

  if (!user) {
    return <LoginPage onLoggedIn={setUser} />;
  }

  return(
    <div>
      <Header linkClicked={(page)=>changeVisibility(page)}/>
      <div style={{paddingTop: '32px'}}>
        {currentPage==="math" && <MathProblem />}
        {currentPage==="courses" && <CourseList />}
        {currentPage==="settings" && <Settings onLoggedOut={handleLoggedOut} />}
      </div>
    </div>
  );
}

export default App;
