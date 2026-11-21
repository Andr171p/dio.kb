import { kbApi } from '@shared/api';
import type {
  AnswerAccepted,
  AnswerFeedback,
  AnswerRun,
  CreateAnswerInput,
  PutFeedbackInput,
} from './types';

const BASE = '/api/user/v1/answers';

export async function createAnswer(
  input: CreateAnswerInput,
  options?: { idempotencyKey?: string; signal?: AbortSignal },
): Promise<AnswerAccepted> {
  return kbApi.post<AnswerAccepted>(BASE, {
    body: {
      question: input.question,
      spaceIds: input.spaceIds?.length ? input.spaceIds : undefined,
    },
    signal: options?.signal,
    headers: options?.idempotencyKey
      ? { 'Idempotency-Key': options.idempotencyKey }
      : undefined,
  });
}

export function getAnswer(
  answerId: string,
  signal?: AbortSignal,
): Promise<AnswerRun> {
  return kbApi.get<AnswerRun>(`${BASE}/${answerId}`, { signal });
}

export function putAnswerFeedback(
  answerId: string,
  input: PutFeedbackInput,
  signal?: AbortSignal,
): Promise<AnswerFeedback> {
  return kbApi.put<AnswerFeedback>(`${BASE}/${answerId}/feedback`, {
    body: {
      helpful: input.helpful,
      reason: input.reason ?? undefined,
      comment: input.comment ?? undefined,
    },
    signal,
  });
}

export function answerEventsPath(answerId: string): string {
  return `${BASE}/${answerId}/events`;
}
