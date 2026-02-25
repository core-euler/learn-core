import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, NavLink, Outlet, useOutletContext, useParams } from 'react-router-dom';
import { api } from '../api/client';
import type { AppShellContext } from '../layouts/AppLayout';
import type { LessonContentResponse } from '../types/api';
import { ApiError } from '../utils/http';

type LessonWorkspaceContext = {
  lessonId: string;
};

export function LessonWorkspacePage() {
  const { lessonId = '' } = useParams();
  const [content, setContent] = useState<LessonContentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [locked, setLocked] = useState(false);
  const [loading, setLoading] = useState(true);
  const { progress } = useOutletContext<AppShellContext>();

  const loadLesson = useCallback(async () => {
    setLoading(true);
    setError(null);
    setLocked(false);
    try {
      const response = await api.lessonContent(lessonId);
      setContent(response);
    } catch (e) {
      if (e instanceof ApiError && e.detail === 'lesson_locked') {
        setLocked(true);
        return;
      }
      setError('Ошибка загрузки урока');
    } finally {
      setLoading(false);
    }
  }, [lessonId]);

  useEffect(() => {
    void loadLesson();
  }, [loadLesson]);

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

  if (loading) return <p>Loading lesson...</p>;
  if (error) {
    return (
      <section>
        <p className="error">{error}</p>
        <button type="button" onClick={() => void loadLesson()}>Повторить</button>
      </section>
    );
  }
  if (!content) return <p>Материал урока недоступен.</p>;

  return (
    <section className="workspace">
      <header className="workspace-head">
        <h1>{content.title}</h1>
        {progressLabel && <p className="muted">Прогресс модуля: {progressLabel}</p>}
      </header>

      <div className="mode-tabs">
        <NavLink to="lecture">Lecture</NavLink>
        <NavLink to="exam">Exam</NavLink>
        <NavLink to="consultant">Consultant</NavLink>
      </div>

      <div className="workspace-chat-zone">
        <Outlet context={{ lessonId } satisfies LessonWorkspaceContext} />
      </div>

      <article className="lesson-material">
        <h3>Материал урока</h3>
        <pre>{content.content}</pre>
      </article>
    </section>
  );
}
