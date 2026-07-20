import './Header.css';

function Header(props) {
    const { currentPage } = props;
    return (
        <header className="header">
            <span className="header-logo">Solveki</span>
            <nav className="header-nav">
                <button className={currentPage === "math" ? "active" : ""} onClick={() => props.linkClicked("math")}>Practice</button>
                <button className={currentPage === "courses" ? "active" : ""} onClick={() => props.linkClicked("courses")}>Available Courses</button>
                <button className={currentPage === "settings" ? "active" : ""} onClick={() => props.linkClicked("settings")}>Settings</button>
            </nav>
        </header>
    );
}

export default Header;
