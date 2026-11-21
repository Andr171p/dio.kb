import type { AnswerProgressEvent, AnswerRunStatus, AnswerStage } from './types';

/** Человекочитаемый этап для живого UX без процентов и таймеров. */
export function progressLabel(event: {
  status: AnswerRunStatus;
  stage: AnswerStage | null;
  resultsCount?: number | null;
  sourcesCount?: number | null;
  connection?: 'connected' | 'disconnected' | 'reconnecting';
}): string {
  if (event.connection === 'reconnecting' || event.connection === 'disconnected')
    return 'Восстанавливаем соединение';

  switch (event.status) {
    case 'queued':
      return 'Приняли ваш вопрос…';
    case 'failed':
      return 'Не удалось сформировать ответ';
    case 'cancelled':
      return 'Генерация отменена';
    case 'completed':
      return 'Ответ готов';
    case 'running':
      break;
  }

  switch (event.stage) {
    case 'retrieval':
      if (event.resultsCount != null) {
        const sources =
          event.sourcesCount != null
            ? ` · выбрано источников: ${event.sourcesCount}`
            : '';
        return `Найдено материалов: ${event.resultsCount}${sources}`;
      }
      return 'Ищем материалы…';
    case 'context_preparation':
      return 'Подготавливаем источники…';
    case 'generation':
      return 'Формируем ответ…';
    case 'validation':
      return 'Проверяем ссылки…';
    default:
      return 'Разбираем ваш вопрос…';
  }
}

export function isTerminalStatus(status: AnswerRunStatus): boolean {
  return status === 'completed' || status === 'failed' || status === 'cancelled';
}

export function applyProgressEvent(
  previous: AnswerProgressEvent | null,
  next: AnswerProgressEvent,
): AnswerProgressEvent | null {
  if (previous && next.sequence <= previous.sequence) return previous;
  return next;
}
