import { logout } from './auth.js';
import OverflowMenu from './ui/OverflowMenu.jsx';
import './Header.css';

// Nav entries per role. Students keep the original practice-focused nav plus
// Assignments; teachers get three primary areas, with the guide behind "?" and
// settings in the account menu.
const STUDENT_NAV = [
  { page: "math", label: "Practice" },
  { page: "dashboard", label: "Dashboard" },
  { page: "courses", label: "Available Courses" },
  { page: "student-classes", label: "Classes" },
  { page: "assignments", label: "Assignments" },
  { page: "settings", label: "Settings" },
];

const TEACHER_NAV = [
  { page: "teacher-overview", label: "Home" },
  { page: "classes", label: "Classes" },
  { page: "teacher-assignments", label: "Assignments" },
];

// Detail pages light up the nav area they belong to.
const NAV_PARENT = {
  "class-detail": "classes",
  "student-detail": "classes",
  "assignment-detail": "teacher-assignments",
  "assignment-builder": "teacher-assignments",
};

function initials(name) {
  const parts = (name || "").trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  return (parts[0][0] + (parts.length > 1 ? parts[parts.length - 1][0] : "")).toUpperCase();
}

function Header(props) {
    const { currentPage, role, user, onLoggedOut } = props;
    const teacher = role === "teacher";
    const nav = teacher ? TEACHER_NAV : STUDENT_NAV;
    const activePage = NAV_PARENT[currentPage] || currentPage;

    async function handleLogout() {
        try {
            await logout();
        } finally {
            onLoggedOut?.();
        }
    }

    return (
        <header className={`header${teacher ? " header-teacher" : ""}`}>
            <span className="header-logo">
                <span className="header-logo-mark" aria-hidden="true">S</span>
                Solveki
            </span>
            <nav className="header-nav">
                {nav.map(({ page, label }) => (
                    <button
                        key={page}
                        className={activePage === page ? "active" : ""}
                        aria-current={activePage === page ? "page" : undefined}
                        onClick={() => props.linkClicked(page)}
                    >
                        {label}
                    </button>
                ))}
            </nav>
            {teacher && (
                <div className="header-tools">
                    <button
                        type="button"
                        className={`header-help${currentPage === "teacher-guide" ? " active" : ""}`}
                        aria-label="Guide"
                        title="How Solveki works"
                        onClick={() => props.linkClicked("teacher-guide")}
                    >
                        ?
                    </button>
                    <OverflowMenu
                        label="Account"
                        trigger={initials(user?.name)}
                        triggerClassName={`header-avatar${currentPage === "settings" ? " active" : ""}`}
                        items={[
                            { label: "Settings", onSelect: () => props.linkClicked("settings") },
                            { label: "Log out", onSelect: handleLogout },
                        ]}
                    />
                </div>
            )}
        </header>
    );
}

export default Header;
