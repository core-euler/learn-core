import { useState } from 'react';
import type { FormEvent } from 'react';
import { useOutletContext } from 'react-router-dom';
import { api } from '../api/client';
import { streamLecture } from '../api/lectureStream';
import { ApiError, mapLimitDetail } from '../utils/http';

type Ctx = { lessonId: string; onLessonCompleted: () => Promise<void> };

type PendingRequest = {
  text: string;
  messageId: string;
};

export function LectureModePage() {
  const { lessonId, onLessonCompleted } = useOutletContext<Ctx>();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Array<{ role: string; text: string }>>([
    { role: 'assistant', text: 'Добро пожаловать в лекцию. Задайте вопрос по материалу.' },
  ]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [lastEventId, setLastEventId] = useState<string | undefined>();
  const [reconnectAttempt, setReconnectAttempt] = useState<number>(0);
  const [pendingRequest, setPendingRequest] = useState<PendingRequest | null>(null);
  const [completionState, setCompletionState] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');

  const updateAssistant = (chunk: string) => {
    setMessages((prev) => {
      const copy = [...prev];
      const last = copy[copy.length - 1];
      copy[copy.length - 1] = { ...last, text: `${last.text}${chunk}` };
      return copy;
    });
  };

  const removeLastAssistant = () => {
    setMessages((prev) => {
      const copy = [...prev];
      if (copy.length > 0 && copy[copy.length - 1]?.role === 'assistant') copy.pop();
      return copy;
    });
  };

  async function runLectureStream(text: string, messageId: string): Promise<boolean> {
    setIsStreaming(true);
    setStreamError(null);
    setReconnectAttempt(0);
    setPendingRequest({ text, messageId });

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
      setPendingRequest(null);
      return true;
    } catch (e) {
      if (e instanceof ApiError && e.status === 429) {
        setStreamError(mapLimitDetail(e.detail));
      } else {
        setStreamError('Ошибка потока. Нажмите «Повторить» для реконнекта или fallback.');
      }
      return false;
    } finally {
      setIsStreaming(false);
    }
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    const text = input.trim();
    const messageId = crypto.randomUUID();
    setMessages((m) => [...m, { role: 'user', text }, { role: 'assistant', text: '' }]);
    setInput('');
    await runLectureStream(text, messageId);
  }

  async function retryLast() {
    if (!pendingRequest || isStreaming) return;

    const streamOk = await runLectureStream(pendingRequest.text, pendingRequest.messageId);
    if (streamOk) return;

    try {
      const fallback = await api.lectureJson(lessonId, pendingRequest.text, pendingRequest.messageId);
      setMessages((prev) => {
        const copy = [...prev];
        copy[copy.length - 1] = { role: 'assistant', text: fallback.reply };
        return copy;
      });
      setStreamError(null);
      setPendingRequest(null);
    } catch {
      removeLastAssistant();
      setMessages((m) => [...m, { role: 'assistant', text: 'Не удалось восстановить поток. Попробуйте отправить вопрос ещё раз.' }]);
      setStreamError('Поток не восстановлен. Можно отправить вопрос заново.');
    }
  }

  async function completeLesson() {
    if (completionState === 'submitting') return;
    setCompletionState('submitting');
    try {
      await onLessonCompleted();
      setCompletionState('success');
    } catch {
      setCompletionState('error');
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
      {!!streamError && !!pendingRequest && (
        <button type="button" className="ghost-btn" onClick={() => void retryLast()} disabled={isStreaming}>
          Повторить
        </button>
      )}
      <form onSubmit={submit} className="composer">
        <input value={input} onChange={(e) => setInput(e.target.value)} maxLength={4000} placeholder="Ваш вопрос" />
        <button type="submit" disabled={isStreaming}>Send</button>
      </form>
      <button className="ghost-btn" onClick={() => void completeLesson()} disabled={completionState === 'submitting'}>
        {completionState === 'submitting' ? 'Завершаем...' : 'Завершить урок'}
      </button>
      {completionState === 'success' && <p className="muted">Урок отмечен как завершённый. Прогресс обновлён.</p>}
      {completionState === 'error' && <p className="error">Не удалось завершить урок. Попробуйте ещё раз.</p>}
    </div>
  );
}
