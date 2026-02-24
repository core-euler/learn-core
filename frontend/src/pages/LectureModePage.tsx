import { useState } from 'react';
import type { FormEvent } from 'react';
import { useOutletContext } from 'react-router-dom';
import { api } from '../api/client';
import { streamLecture } from '../api/lectureStream';
import { ApiError, mapLimitDetail } from '../utils/http';

type Ctx = { lessonId: string };

export function LectureModePage() {
  const { lessonId } = useOutletContext<Ctx>();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Array<{ role: string; text: string }>>([
    { role: 'assistant', text: 'Добро пожаловать в лекцию. Задайте вопрос по материалу.' },
  ]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [lastEventId, setLastEventId] = useState<string | undefined>();
  const [reconnectAttempt, setReconnectAttempt] = useState<number>(0);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    const text = input.trim();
    const messageId = crypto.randomUUID();
    setMessages((m) => [...m, { role: 'user', text }, { role: 'assistant', text: '' }]);
    setInput('');
    setIsStreaming(true);
    setStreamError(null);
    setReconnectAttempt(0);

    const updateAssistant = (chunk: string) => {
      setMessages((prev) => {
        const copy = [...prev];
        const last = copy[copy.length - 1];
        copy[copy.length - 1] = { ...last, text: `${last.text}${chunk}` };
        return copy;
      });
    };

    try {
      await streamLecture({
        lessonId,
        message: text,
        messageId,
        lastEventId,
        handlers: {
          onChunk: (chunk) => updateAssistant(chunk),
          onEventId: (id) => setLastEventId(id),
          onDone: () => undefined,
          onReconnectAttempt: (attempt) => setReconnectAttempt(attempt),
        },
      });
    } catch (e) {
      if (e instanceof ApiError && e.status === 429) {
        setStreamError(mapLimitDetail(e.detail));
      } else {
        setStreamError('Ошибка потока. Нажмите повторить.');
        try {
          const fallback = await api.lectureJson(lessonId, text, messageId);
          setMessages((prev) => {
            const copy = [...prev];
            copy[copy.length - 1] = { role: 'assistant', text: fallback.reply };
            return copy;
          });
        } catch {
          // keep recoverable error
        }
      }
    } finally {
      setIsStreaming(false);
    }
  }

  return (
    <div className="chat-panel">
      <div className="chat-log">
        {messages.map((m, i) => (
          <p key={i} className={`msg msg-${m.role}`}>
            <b>{m.role}:</b> {m.text}
          </p>
        ))}
      </div>
      {isStreaming && <p className="muted">Генерация ответа...</p>}
      {reconnectAttempt > 0 && isStreaming && <p className="muted">Переподключение потока… попытка {reconnectAttempt}</p>}
      {streamError && <p className="error">{streamError}</p>}
      <form onSubmit={submit} className="composer">
        <input value={input} onChange={(e) => setInput(e.target.value)} maxLength={4000} placeholder="Ваш вопрос" />
        <button type="submit" disabled={isStreaming}>Send</button>
      </form>
      <button className="ghost-btn" onClick={() => api.completeLesson(lessonId)}>Завершить урок</button>
    </div>
  );
}
