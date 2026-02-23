import { API_BASE, ApiError } from '../utils/http';

type StreamHandlers = {
  onChunk: (chunk: string) => void;
  onDone: () => void;
  onEventId?: (id: string) => void;
};

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

export async function streamLecture(args: {
  lessonId: string;
  message: string;
  messageId: string;
  lastEventId?: string;
  handlers: StreamHandlers;
}) {
  const headers = new Headers({
    Accept: 'text/event-stream',
    'Content-Type': 'application/json',
  });
  const csrf = getCookie('csrf_token');
  if (csrf) headers.set('x-csrf-token', csrf);
  if (args.lastEventId) headers.set('Last-Event-ID', args.lastEventId);

  const res = await fetch(`${API_BASE}/api/chat/lecture`, {
    method: 'POST',
    credentials: 'include',
    headers,
    body: JSON.stringify({ lesson_id: args.lessonId, message: args.message, message_id: args.messageId }),
  });

  if (!res.ok || !res.body) {
    let detail = 'request_failed';
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split('\n\n');
    buffer = events.pop() ?? '';

    for (const eventBlock of events) {
      const lines = eventBlock.split('\n');
      const type = lines.find((l) => l.startsWith('event:'))?.replace('event:', '').trim();
      const id = lines.find((l) => l.startsWith('id:'))?.replace('id:', '').trim();
      const dataRaw = lines.find((l) => l.startsWith('data:'))?.replace('data:', '').trim();
      if (!type || !dataRaw) continue;
      if (id) args.handlers.onEventId?.(id);
      const data = JSON.parse(dataRaw);
      if (type === 'chunk') args.handlers.onChunk(data.content ?? '');
      if (type === 'done') args.handlers.onDone();
    }
  }
}
