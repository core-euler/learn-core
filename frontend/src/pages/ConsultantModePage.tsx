import { useState } from 'react';
import type { FormEvent } from 'react';
import { useProgress } from '../hooks/useProgress';
import { api } from '../api/client';
import { ApiError, mapLimitDetail } from '../utils/http';

export function ConsultantModePage() {
  const { data: progress } = useProgress();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Array<{ q: string; a: string; source: string }>>([]);
  const [error, setError] = useState<string | null>(null);

  if (!progress) return <p>Loading consultant...</p>;
  if (!progress.consultant_unlocked) {
    return <p>Консультант откроется после завершения минимум одного модуля.</p>;
  }

  async function ask(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;
    setError(null);
    setInput('');
    try {
      const response = await api.consultant(text, crypto.randomUUID());
      setMessages((prev) => [...prev, { q: text, a: response.reply, source: response.source }]);
    } catch (e) {
      if (e instanceof ApiError && e.status === 429) setError(mapLimitDetail(e.detail));
      else if (e instanceof ApiError && e.detail === 'consultant_locked') setError('Режим пока недоступен по прогрессу.');
      else setError('Ошибка консультанта');
    }
  }

  return (
    <div>
      <h3>Consultant</h3>
      {messages.map((m, i) => (
        <div key={i}>
          <p><b>Q:</b> {m.q}</p>
          <p><b>A:</b> {m.a}</p>
          <small>source: {m.source}</small>
        </div>
      ))}
      {error && <p className="error">{error}</p>}
      <form onSubmit={ask}>
        <input value={input} onChange={(e) => setInput(e.target.value)} maxLength={4000} />
        <button type="submit">Ask</button>
      </form>
    </div>
  );
}
