import { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { api } from '../api/client';
import type { ExamFinishResponse, ExamStartResponse } from '../types/api';

type Ctx = { lessonId: string };

export function ExamModePage() {
  const { lessonId } = useOutletContext<Ctx>();
  const [exam, setExam] = useState<ExamStartResponse | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<ExamFinishResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [isFinishing, setIsFinishing] = useState(false);

  const start = async () => {
    setResult(null);
    setError(null);
    setIsStarting(true);
    try {
      setExam(await api.examStart(lessonId));
    } catch {
      setError('Не удалось запустить экзамен.');
    } finally {
      setIsStarting(false);
    }
  };

  const finish = async () => {
    if (!exam || isFinishing) return;
    setError(null);
    setIsFinishing(true);
    try {
      const payload = Object.entries(answers).map(([question_id, answer]) => ({ question_id, answer }));
      setResult(await api.examFinish(exam.session_id, payload));
    } catch {
      setError('Не удалось завершить экзамен. Проверьте ответы и повторите.');
    } finally {
      setIsFinishing(false);
    }
  };

  return (
    <div className="chat-panel">
      {!exam ? (
        <div>
          <button onClick={start} disabled={isStarting}>{isStarting ? 'Starting...' : 'Start exam'}</button>
          {error && (
            <div>
              <p className="error">{error}</p>
              <button type="button" onClick={start} disabled={isStarting}>Повторить</button>
            </div>
          )}
        </div>
      ) : (
        <div>
          {exam.questions.length === 0 && <p className="muted">Вопросы пока не получены.</p>}
          {exam.questions.map((q) => (
            <div key={q.id}>
              <p>{q.text}</p>
              {q.options?.length ? (
                <select onChange={(e) => setAnswers((a) => ({ ...a, [q.id]: e.target.value }))} defaultValue="">
                  <option value="" disabled>Выберите ответ</option>
                  {q.options.map((o) => <option key={o} value={o}>{o}</option>)}
                </select>
              ) : (
                <input onChange={(e) => setAnswers((a) => ({ ...a, [q.id]: e.target.value }))} />
              )}
            </div>
          ))}
          <button onClick={finish} disabled={isFinishing}>{isFinishing ? 'Finishing...' : 'Finish exam'}</button>
          {error && <p className="error">{error}</p>}
        </div>
      )}

      {result && (
        <div>
          <p>Score: {result.score}%</p>
          <p>{result.passed ? 'PASS' : 'FAIL'}</p>
        </div>
      )}
    </div>
  );
}
