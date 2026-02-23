import { useEffect, useMemo, useState } from 'react';
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
  const { data: progress } = useProgress();

  useEffect(() => {
    if (!moduleId) return;
    api.moduleById(moduleId).then(setModule).catch(() => setError('Ошибка загрузки модуля'));
  }, [moduleId]);

  const lessonStatuses = useMemo(() => {
    const statuses = new Map<string, LessonStatus>();
    progress?.modules.forEach((m) => m.lessons.forEach((l) => statuses.set(l.lesson_id, l.status)));
    return statuses;
  }, [progress]);

  if (error) return <p>{error}</p>;
  if (!module) return <p>Loading module...</p>;

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
