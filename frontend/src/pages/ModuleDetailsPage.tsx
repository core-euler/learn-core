import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../api/client';
import { useProgress } from '../hooks/useProgress';
import type { ModuleDetailsResponse, LessonStatus } from '../types/api';

const statusLabel: Record<LessonStatus, string> = {
  locked: 'Locked',
  available: 'Available',
  completed: 'Completed',
};

export function ModuleDetailsPage() {
  const { moduleId } = useParams();
  const [module, setModule] = useState<ModuleDetailsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const { data: progress } = useProgress();

  const loadModule = useCallback(async () => {
    if (!moduleId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await api.moduleById(moduleId);
      setModule(response);
    } catch {
      setError('Ошибка загрузки модуля');
    } finally {
      setLoading(false);
    }
  }, [moduleId]);

  useEffect(() => {
    void loadModule();
  }, [loadModule]);

  const lessonStatuses = useMemo(() => {
    const statuses = new Map<string, LessonStatus>();
    progress?.modules.forEach((m) => m.lessons.forEach((l) => statuses.set(l.lesson_id, l.status)));
    return statuses;
  }, [progress]);

  if (loading) return <p>Loading module...</p>;
  if (error) {
    return (
      <section>
        <p className="error">{error}</p>
        <button type="button" onClick={() => void loadModule()}>Повторить</button>
      </section>
    );
  }
  if (!module) return <p>Модуль не найден.</p>;

  return (
    <section>
      <h1>{module.title}</h1>
      <ul>
        {module.lessons.map((lesson) => {
          const status = lessonStatuses.get(lesson.id) ?? 'locked';
          const isLocked = status === 'locked';
          return (
            <li key={lesson.id}>
              <span>{lesson.title} — {statusLabel[status]}</span>{' '}
              {isLocked ? (
                <span className="muted">Недоступно</span>
              ) : (
                <Link to={`/lessons/${lesson.id}/lecture`}>Открыть</Link>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
