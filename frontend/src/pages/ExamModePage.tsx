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

  const start = async () => {
    setResult(null);
    setExam(await api.examStart(lessonId));
  };

  const finish = async () => {
    if (!exam) return;
    const payload = Object.entries(answers).map(([question_id, answer]) => ({ question_id, answer }));
    setResult(await api.examFinish(exam.session_id, payload));
  };

  return (
    <div>
      <h3>Exam</h3>
      {!exam ? (
        <button onClick={start}>Start exam</button>
      ) : (
        <div>
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
          <button onClick={finish}>Finish exam</button>
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
