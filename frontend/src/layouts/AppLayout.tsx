import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useProgress } from '../hooks/useProgress';
import type { LessonStatus, ProgressResponse } from '../types/api';

type AppShellContext = {
  progress: ProgressResponse | null;
  progressLoading: boolean;
  progressError: string | null;
  reloadProgress: () => Promise<void>;
};

const statusSymbol: Record<LessonStatus, string> = {
  locked: '●',
  available: '◐',
  completed: '✓',
};

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { data: progress, loading: progressLoading, error: progressError, reload: reloadProgress } = useProgress();

  const activeLessonId = location.pathname.match(/^\/lessons\/([^/]+)/)?.[1] ?? null;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-head">
          <Link to="/dashboard" className="brand-link">LLM Handbook</Link>
          <p className="muted">Курс</p>
        </div>

        <nav className="course-nav" aria-label="Course navigation">
          {progressLoading && <p className="muted">Загрузка структуры курса...</p>}
          {progressError && (
            <button className="ghost-btn" onClick={() => void reloadProgress()}>
              Повторить загрузку курса
            </button>
          )}
          {progress &&
            progress.modules.map((module, moduleIndex) => (
              <section key={module.module_id} className="module-group">
                <NavLink to={`/modules/${module.module_id}`} className="module-link">
                  <span>Модуль {moduleIndex + 1}</span>
                  <span className="muted">{module.status}</span>
                </NavLink>
                <ul>
                  {module.lessons.map((lesson, lessonIndex) => {
                    const isLocked = lesson.status === 'locked';
                    const isActive = activeLessonId === lesson.lesson_id;
                    return (
                      <li key={lesson.lesson_id}>
                        {isLocked ? (
                          <span className="lesson-link muted">
                            {statusSymbol[lesson.status]} Урок {lessonIndex + 1}
                          </span>
                        ) : (
                          <NavLink
                            to={`/lessons/${lesson.lesson_id}/lecture`}
                            className={`lesson-link ${isActive ? 'active' : ''}`.trim()}
                          >
                            {statusSymbol[lesson.status]} Урок {lessonIndex + 1}
                          </NavLink>
                        )}
                      </li>
                    );
                  })}
                </ul>
              </section>
            ))}
        </nav>
      </aside>

      <div className="main-shell">
        <header className="main-topbar">
          <nav>
            <NavLink to="/dashboard">Dashboard</NavLink>
            <NavLink to="/modules">Modules</NavLink>
            <NavLink to="/profile">Profile</NavLink>
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

        <main className="chat-main">
          <Outlet
            context={
              {
                progress,
                progressLoading,
                progressError,
                reloadProgress,
              } satisfies AppShellContext
            }
          />
        </main>
      </div>
    </div>
  );
}

export type { AppShellContext };
