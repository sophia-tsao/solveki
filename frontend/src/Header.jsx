import './Header.css';

// Nav entries per role. Students keep the original practice-focused nav plus
// Assignments; teachers get the class/assignment authoring and analytics pages.
const STUDENT_NAV = [
  { page: "math", label: "Practice" },
  { page: "dashboard", label: "Dashboard" },
  { page: "courses", label: "Available Courses" },
  { page: "student-classes", label: "Classes" },
  { page: "assignments", label: "Assignments" },
  { page: "settings", label: "Settings" },
];

const TEACHER_NAV = [
  { page: "teacher-overview", label: "Overview" },
  { page: "classes", label: "Classes" },
  { page: "teacher-assignments", label: "Assignments" },
  { page: "teacher-guide", label: "Guide" },
  { page: "settings", label: "Settings" },
];

function Header(props) {
    const { currentPage, role } = props;
    const nav = role === "teacher" ? TEACHER_NAV : STUDENT_NAV;
    return (
        <header className="header">
            <span className="header-logo">Solveki</span>
            <nav className="header-nav">
                {nav.map(({ page, label }) => (
                    <button
                        key={page}
                        className={currentPage === page ? "active" : ""}
                        onClick={() => props.linkClicked(page)}
                    >
                        {label}
                    </button>
                ))}
            </nav>
        </header>
    );
}

export default Header;
