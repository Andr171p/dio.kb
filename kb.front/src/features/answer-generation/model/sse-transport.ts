import { kbApi } from '@shared/api';
import {
  answerEventsPath,
  type AnswerProgressEvent,
} from '@entities/answer';

export type SseConnectionState =
  | 'idle'
  | 'connecting'
  | 'connected'
  | 'reconnecting'
  | 'disconnected'
  | 'closed';

interface SubscribeOptions {
  answerId: string;
  signal: AbortSignal;
  onEvent: (event: AnswerProgressEvent) => void;
  onConnection: (state: SseConnectionState) => void;
  /** Last-Event-ID для возобновления после обрыва */
  lastEventId?: number | null;
}

/**
 * Fetch-based SSE: EventSource не умеет Authorization: Bearer.
 * Переподключение с Last-Event-ID делает вызывающий код.
 */
export async function subscribeAnswerEvents({
  answerId,
  signal,
  onEvent,
  onConnection,
  lastEventId,
}: SubscribeOptions): Promise<void> {
  onConnection(lastEventId != null ? 'reconnecting' : 'connecting');

  const response = await kbApi.send('GET', answerEventsPath(answerId), {
    signal,
    headers: {
      Accept: 'text/event-stream',
      ...(lastEventId != null ? { 'Last-Event-ID': String(lastEventId) } : {}),
    },
  });

  if (!response.ok || !response.body) {
    throw new Error(`SSE unavailable (${response.status})`);
  }

  onConnection('connected');

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let separator = buffer.indexOf('\n\n');
      while (separator >= 0) {
        const raw = buffer.slice(0, separator);
        buffer = buffer.slice(separator + 2);
        const parsed = parseSseFrame(raw);
        if (parsed) onEvent(parsed);
        separator = buffer.indexOf('\n\n');
      }
    }
  } finally {
    reader.releaseLock();
    if (!signal.aborted) onConnection('closed');
  }
}

function parseSseFrame(raw: string): AnswerProgressEvent | null {
  let data = '';
  for (const line of raw.split('\n')) {
    if (line.startsWith(':')) continue;
    if (line.startsWith('data:')) {
      data += (data ? '\n' : '') + line.slice(5).trimStart();
    }
  }
  if (!data) return null;

  try {
    const payload = JSON.parse(data) as AnswerProgressEvent;
    if (
      typeof payload.sequence !== 'number' ||
      typeof payload.status !== 'string'
    )
      return null;
    return payload;
  } catch {
    return null;
  }
}
