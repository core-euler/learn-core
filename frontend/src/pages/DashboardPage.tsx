import { Link } from 'react-router-dom';
import { useProgress } from '../hooks/useProgress';

export function DashboardPage() {
  const { data, loading, error, reload } = useProgress();

  if (loading) return <p>Loading dashboard...</p>;
  if (error) return <button onClick={reload}>Retry dashboard</button>;
  if (!data) return <p>Нет данных</p>;

  return (
    <section>
      <h1>Dashboard</h1>
      <p>Общий прогресс: {data.overall_percent}%</p>
      {data.next_lesson_id ? (
        <Link to={`/lessons/${data.next_lesson_id}/lecture`} className="btn">
          Продолжить
        </Link>
      ) : (
        <div className="empty">Доступных уроков сейчас нет. Завершите текущий модуль.</div>
      )}
    </section>
  );
}
