import { useState } from 'react';
import type { FormEvent } from 'react';
import { useProgress } from '../hooks/useProgress';
import { api } from '../api/client';
import { ApiError, mapLimitDetail } from '../utils/http';

export function ConsultantModePage() {
  const { data: progress, loading: progressLoading, error: progressError, reload: reloadProgress } = useProgress();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Array<{ q: string; a: string; source: string }>>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (progressLoading) return <p>Loading consultant...</p>;
  if (progressError) {
    return (
      <section>
        <p className="error">Ошибка загрузки прогресса для консультанта.</p>
        <button type="button" onClick={() => void reloadProgress()}>Повторить</button>
      </section>
    );
  }
  if (!progress) return <p>Данные прогресса недоступны.</p>;
  if (!progress.consultant_unlocked) {
    return <p>Консультант откроется после завершения минимум одного модуля.</p>;
  }

  async function ask(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || isSubmitting) return;
    setError(null);
    setInput('');
    setIsSubmitting(true);
    try {
      const response = await api.consultant(text, crypto.randomUUID());
      setMessages((prev) => [...prev, { q: text, a: response.reply, source: response.source }]);
    } catch (e) {
      if (e instanceof ApiError && e.status === 429) setError(mapLimitDetail(e.detail));
      else if (e instanceof ApiError && e.detail === 'consultant_locked') setError('Режим пока недоступен по прогрессу.');
      else setError('Ошибка консультанта');
      setInput(text);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="chat-panel">
      {messages.length === 0 && <p className="muted">Пока нет сообщений. Задайте первый вопрос.</p>}
      {messages.map((m, i) => (
        <div key={i} className="msg msg-assistant">
          <p><b>Q:</b> {m.q}</p>
          <p><b>A:</b> {m.a}</p>
          <small>source: {m.source}</small>
        </div>
      ))}
      {isSubmitting && <p className="muted">Консультант отвечает…</p>}
      {error && <p className="error">{error}</p>}
      <form onSubmit={ask} className="composer">
        <input value={input} onChange={(e) => setInput(e.target.value)} maxLength={4000} />
        <button type="submit" disabled={isSubmitting}>Ask</button>
      </form>
    </div>
  );
}
