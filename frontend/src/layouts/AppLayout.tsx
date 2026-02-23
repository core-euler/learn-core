import { Link, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">LLM Handbook</div>
        <nav>
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/modules">Modules</Link>
          <Link to="/profile">Profile</Link>
        </nav>
        <div className="userbox">
          <span>{user?.first_name}</span>
          <button
            onClick={async () => {
              await logout();
              navigate('/login');
            }}
          >
            Logout
          </button>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
