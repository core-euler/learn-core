import { Link, useOutletContext } from 'react-router-dom';
import type { AppShellContext } from '../layouts/AppLayout';

export function DashboardPage() {
  const { progress, progressLoading, progressError, reloadProgress } = useOutletContext<AppShellContext>();

  if (progressLoading) return <p>Loading dashboard...</p>;
  if (progressError) return <button onClick={() => void reloadProgress()}>Retry dashboard</button>;
  if (!progress) return <p>Нет данных</p>;

  return (
    <section>
      <h1>Dashboard</h1>
      <p>Общий прогресс: {progress.overall_percent}%</p>
      {progress.next_lesson_id ? (
        <Link to={`/lessons/${progress.next_lesson_id}/lecture`} className="primary-btn">
          Продолжить
        </Link>
      ) : (
        <div className="empty">Доступных уроков сейчас нет. Завершите текущий модуль.</div>
      )}
    </section>
  );
}
