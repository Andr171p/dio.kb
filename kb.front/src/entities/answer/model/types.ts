/** Статус долгоживущего AnswerRun на backend. */
export type AnswerRunStatus =
  | 'queued'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled';

/** Этап пайплайна внутри running. */
export type AnswerStage =
  | 'retrieval'
  | 'context_preparation'
  | 'generation'
  | 'validation';

/** Итог проверки evidence после генерации. */
export type AnswerStatus =
  | 'answered'
  | 'insufficient_evidence'
  | 'conflicting_evidence';

export type FeedbackReason =
  | 'no_solution'
  | 'incorrect'
  | 'incomplete'
  | 'outdated'
  | 'irrelevant_sources'
  | 'other';

export interface AnswerSource {
  id: string;
  articleId: string;
  revisionId: string;
  chunkId: string;
  title: string;
  url: string;
  excerpt: string;
  anchor: string | null;
}

export interface AnswerBlock {
  markdown: string;
  citations: string[];
}

export interface AnswerResponse {
  id: string;
  status: AnswerStatus;
  blocks: AnswerBlock[];
  sources: AnswerSource[];
  missingContext: string[];
}

export interface AnswerAccepted {
  id: string;
  status: AnswerRunStatus;
  eventsUrl: string;
  resultUrl: string;
}

export interface AnswerUsage {
  inputTokens: number;
  outputTokens: number;
  cachedInputTokens: number;
  reasoningTokens: number | null;
  estimatedCostUsd: string | null;
}

/** GET /answers/{id} — актуальное состояние run и готовый ответ. */
export interface AnswerRun {
  id: string;
  organizationId: string;
  principalId: string;
  principalType: string;
  status: AnswerRunStatus;
  stage: AnswerStage | null;
  stageSequence: number;
  question: string | null;
  spaceIds: string[] | null;
  answerStatus: AnswerStatus | null;
  response: AnswerResponse | null;
  resultsCount: number | null;
  sourcesCount: number | null;
  latencyMs: number | null;
  errorCode: string | null;
  createdAt: string;
  startedAt: string | null;
  completedAt: string | null;
  usage?: AnswerUsage | null;
}

export interface AnswerProgressEvent {
  answerId: string;
  sequence: number;
  event: string;
  occurredAt: string;
  status: AnswerRunStatus;
  stage: AnswerStage | null;
  resultsCount: number | null;
  sourcesCount: number | null;
  errorCode: string | null;
}

export interface AnswerFeedback {
  answerId: string;
  helpful: boolean;
  reason: FeedbackReason | null;
  comment: string | null;
}

export interface CreateAnswerInput {
  question: string;
  spaceIds?: string[];
}

export interface PutFeedbackInput {
  helpful: boolean;
  reason?: FeedbackReason | null;
  comment?: string | null;
}
