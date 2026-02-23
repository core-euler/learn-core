import { useEffect, useMemo, useState } from 'react';
import { Link, NavLink, Outlet, useParams } from 'react-router-dom';
import { api } from '../api/client';
import { useProgress } from '../hooks/useProgress';
import type { LessonContentResponse } from '../types/api';
import { ApiError } from '../utils/http';

export function LessonWorkspacePage() {
  const { lessonId = '' } = useParams();
  const [content, setContent] = useState<LessonContentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [locked, setLocked] = useState(false);
  const { data: progress } = useProgress();

  useEffect(() => {
    setError(null);
    setLocked(false);
    api.lessonContent(lessonId)
      .then(setContent)
      .catch((e) => {
        if (e instanceof ApiError && e.detail === 'lesson_locked') {
          setLocked(true);
          return;
        }
        setError('Ошибка загрузки урока');
      });
  }, [lessonId]);

  const progressLabel = useMemo(() => {
    if (!progress) return null;
    const module = progress.modules.find((m) => m.lessons.some((l) => l.lesson_id === lessonId));
    if (!module) return null;
    const done = module.lessons.filter((l) => l.status === 'completed').length;
    return `${done}/${module.lessons.length}`;
  }, [progress, lessonId]);

  if (locked) {
    return (
      <section>
        <h1>Урок заблокирован</h1>
        <p>Этот урок станет доступен после завершения предыдущего.</p>
        <Link to="/modules">Назад к модулям</Link>
      </section>
    );
  }

  if (error) return <p>{error}</p>;
  if (!content) return <p>Loading lesson...</p>;

  return (
    <section>
      <h1>{content.title}</h1>
      {progressLabel && <p>Прогресс модуля: {progressLabel}</p>}
      <div className="mode-tabs">
        <NavLink to="lecture">Lecture</NavLink>
        <NavLink to="exam">Exam</NavLink>
        <NavLink to="consultant">Consultant</NavLink>
      </div>
      <div className="lesson-grid">
        <article>
          <pre>{content.content}</pre>
        </article>
        <aside>
          <Outlet context={{ lessonId }} />
        </aside>
      </div>
    </section>
  );
}
