import { create } from 'zustand';
import {
  applyProgressEvent,
  createAnswer,
  getAnswer,
  isTerminalStatus,
  type AnswerProgressEvent,
  type AnswerRun,
  type CreateAnswerInput,
} from '@entities/answer';
import { ApiError, describeError, isAbortError } from '@shared/api';
import { registerStoreReset } from '@shared/lib/store-reset';
import {
  subscribeAnswerEvents,
  type SseConnectionState,
} from './sse-transport';

type Phase =
  | 'idle'
  | 'starting'
  | 'running'
  | 'ready'
  | 'failed'
  | 'cancelled'
  | 'access_denied';

interface AnswerRunState {
  phase: Phase;
  answerId: string | null;
  question: string | null;
  spaceIds: string[];
  progress: AnswerProgressEvent | null;
  run: AnswerRun | null;
  connection: SseConnectionState;
  error: string | null;
  /** Явный запрос с Quick Search / кнопки — не из useEffect по query */
  autoStart: boolean;
}

const initial: AnswerRunState = {
  phase: 'idle',
  answerId: null,
  question: null,
  spaceIds: [],
  progress: null,
  run: null,
  connection: 'idle',
  error: null,
  autoStart: false,
};

let streamController: AbortController | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let activeAnswerId: string | null = null;

export const useAnswerRun = create<AnswerRunState>()(() => ({ ...initial }));

registerStoreReset(() => {
  stopStream();
  useAnswerRun.setState({ ...initial });
});

function stopStream(clearActive = true) {
  streamController?.abort();
  streamController = null;
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  if (clearActive) activeAnswerId = null;
}

function setPhaseFromRun(run: AnswerRun): Phase {
  if (run.status === 'completed') return 'ready';
  if (run.status === 'failed') return 'failed';
  if (run.status === 'cancelled') return 'cancelled';
  return 'running';
}

async function loadRun(answerId: string, signal?: AbortSignal): Promise<AnswerRun> {
  try {
    return await getAnswer(answerId, signal);
  } catch (error) {
    if (error instanceof ApiError && (error.status === 403 || error.status === 404)) {
      useAnswerRun.setState({
        phase: 'access_denied',
        run: null,
        progress: null,
        error: describeError(error),
      });
    }
    throw error;
  }
}

function scheduleReconnect(answerId: string, lastSequence: number | null) {
  if (reconnectTimer) return;
  useAnswerRun.setState({ connection: 'reconnecting' });
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    void openStream(answerId, lastSequence);
  }, 1200);
}

async function openStream(answerId: string, lastEventId: number | null = null) {
  if (activeAnswerId !== answerId) return;

  // Не сбрасываем activeAnswerId — иначе гонка с SSE-событиями
  stopStream(false);
  activeAnswerId = answerId;
  const controller = new AbortController();
  streamController = controller;

  try {
    await subscribeAnswerEvents({
      answerId,
      signal: controller.signal,
      lastEventId,
      onConnection: (connection) => {
        if (activeAnswerId === answerId)
          useAnswerRun.setState({ connection });
      },
      onEvent: (event) => {
        if (activeAnswerId !== answerId) return;
        const nextProgress = applyProgressEvent(
          useAnswerRun.getState().progress,
          event,
        );
        useAnswerRun.setState({
          progress: nextProgress,
          phase:
            event.status === 'failed'
              ? 'failed'
              : event.status === 'cancelled'
                ? 'cancelled'
                : event.status === 'completed'
                  ? 'running'
                  : 'running',
          error:
            event.status === 'failed'
              ? event.errorCode ?? 'Не удалось сформировать ответ'
              : null,
        });

        if (isTerminalStatus(event.status)) {
          void finalize(answerId, event.status);
        }
      },
    });

    // Поток закрылся без terminal — возможно, ответ уже готов
    if (activeAnswerId === answerId && !controller.signal.aborted) {
      const run = await loadRun(answerId).catch(() => null);
      if (!run || activeAnswerId !== answerId) return;
      if (isTerminalStatus(run.status)) {
        useAnswerRun.setState({
          run,
          phase: setPhaseFromRun(run),
          connection: 'closed',
          error: run.status === 'failed' ? run.errorCode : null,
        });
        return;
      }
      scheduleReconnect(answerId, useAnswerRun.getState().progress?.sequence ?? null);
    }
  } catch (error) {
    if (isAbortError(error) || controller.signal.aborted) return;
    if (activeAnswerId !== answerId) return;

    const snapshot = await loadRun(answerId).catch(() => null);
    if (snapshot && isTerminalStatus(snapshot.status)) {
      useAnswerRun.setState({
        run: snapshot,
        phase: setPhaseFromRun(snapshot),
        connection: 'closed',
        error: snapshot.status === 'failed' ? snapshot.errorCode : null,
      });
      return;
    }

    scheduleReconnect(
      answerId,
      useAnswerRun.getState().progress?.sequence ?? null,
    );
  }
}

async function finalize(answerId: string, status: AnswerRun['status']) {
  stopStream();
  activeAnswerId = answerId;
  try {
    const run = await loadRun(answerId);
    if (activeAnswerId !== answerId) return;
    useAnswerRun.setState({
      run,
      phase: setPhaseFromRun(run),
      connection: 'closed',
      error: status === 'failed' ? run.errorCode ?? 'Не удалось сформировать ответ' : null,
    });
  } catch (error) {
    if (isAbortError(error) || activeAnswerId !== answerId) return;
    useAnswerRun.setState({
      phase: status === 'failed' ? 'failed' : 'access_denied',
      error: describeError(error),
      connection: 'closed',
    });
  } finally {
    activeAnswerId = null;
  }
}

/** Сброс панели без создания нового run. */
export function resetAnswerRun() {
  stopStream();
  useAnswerRun.setState({ ...initial });
}

/**
 * Создать один AnswerRun по явному действию пользователя.
 * Не вызывать из useEffect при смене query.
 */
export async function startAnswerRun(input: CreateAnswerInput): Promise<string | null> {
  const question = input.question.trim();
  if (question.length < 2) return null;

  stopStream();
  useAnswerRun.setState({
    ...initial,
    phase: 'starting',
    question,
    spaceIds: input.spaceIds ?? [],
    autoStart: false,
  });

  try {
    const accepted = await createAnswer({
      question,
      spaceIds: input.spaceIds,
    });
    activeAnswerId = accepted.id;
    useAnswerRun.setState({
      phase: 'running',
      answerId: accepted.id,
      progress: {
        answerId: accepted.id,
        sequence: 0,
        event: 'answer.queued',
        occurredAt: new Date().toISOString(),
        status: 'queued',
        stage: null,
        resultsCount: null,
        sourcesCount: null,
        errorCode: null,
      },
    });
    void openStream(accepted.id);
    return accepted.id;
  } catch (error) {
    useAnswerRun.setState({
      phase: 'failed',
      error: describeError(error),
      connection: 'idle',
    });
    return null;
  }
}

/** Восстановить существующий run после перезагрузки / из URL `answer`. */
export async function restoreAnswerRun(answerId: string) {
  if (!answerId) return;
  const current = useAnswerRun.getState();
  if (
    current.answerId === answerId &&
    (current.phase === 'starting' ||
      current.phase === 'running' ||
      current.phase === 'ready')
  ) {
    return;
  }

  stopStream();
  useAnswerRun.setState({
    ...initial,
    phase: 'starting',
    answerId,
  });

  try {
    const run = await loadRun(answerId);
    activeAnswerId = answerId;
    useAnswerRun.setState({
      answerId,
      question: run.question,
      spaceIds: run.spaceIds ?? [],
      run: isTerminalStatus(run.status) ? run : null,
      phase: setPhaseFromRun(run),
      progress: {
        answerId: run.id,
        sequence: run.stageSequence,
        event: 'answer.snapshot',
        occurredAt: new Date().toISOString(),
        status: run.status,
        stage: run.stage,
        resultsCount: run.resultsCount,
        sourcesCount: run.sourcesCount,
        errorCode: run.errorCode,
      },
      error: run.status === 'failed' ? run.errorCode : null,
    });

    if (!isTerminalStatus(run.status)) void openStream(answerId, run.stageSequence);
    else activeAnswerId = null;
  } catch (error) {
    if (isAbortError(error)) return;
    useAnswerRun.setState({
      phase: 'failed',
      error: describeError(error),
    });
  }
}

/** Повторить генерацию для того же вопроса (новый AnswerRun). */
export async function retryAnswerRun() {
  const { question, spaceIds } = useAnswerRun.getState();
  if (!question) return null;
  return startAnswerRun({ question, spaceIds });
}

/** Флаг из Quick Search: на SearchPage один раз запустить AnswerRun. */
export function markAnswerAutoStart(question: string, spaceIds: string[] = []) {
  useAnswerRun.setState({
    ...initial,
    question,
    spaceIds,
    autoStart: true,
  });
}

export function consumeAnswerAutoStart(): CreateAnswerInput | null {
  const state = useAnswerRun.getState();
  if (!state.autoStart || !state.question) return null;
  useAnswerRun.setState({ autoStart: false });
  return { question: state.question, spaceIds: state.spaceIds };
}
