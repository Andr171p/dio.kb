import { kbApi } from '@shared/api';
import type { GapKind, GapStatus, KnowledgeGap } from './types';

const BASE = '/api/user/v1/knowledge-gaps';

export function listKnowledgeGaps(options?: {
  status?: GapStatus;
  spaceId?: string;
  limit?: number;
  signal?: AbortSignal;
}): Promise<{ items: KnowledgeGap[] }> {
  return kbApi.get<{ items: KnowledgeGap[] }>(BASE, {
    query: {
      status: options?.status,
      spaceId: options?.spaceId,
      limit: options?.limit ?? 50,
    },
    signal: options?.signal,
  });
}

export function getKnowledgeGap(
  gapId: string,
  signal?: AbortSignal,
): Promise<KnowledgeGap> {
  return kbApi.get<KnowledgeGap>(`${BASE}/${gapId}`, { signal });
}

export function patchKnowledgeGap(
  gapId: string,
  body: {
    kind?: GapKind;
    ownerId?: string | null;
    relatedArticleId?: string | null;
  },
): Promise<KnowledgeGap> {
  return kbApi.patch<KnowledgeGap>(`${BASE}/${gapId}`, { body });
}

export function startKnowledgeGap(gapId: string): Promise<KnowledgeGap> {
  return kbApi.post<KnowledgeGap>(`${BASE}/${gapId}/start`);
}

export function resolveKnowledgeGap(
  gapId: string,
  note: string,
): Promise<KnowledgeGap> {
  return kbApi.post<KnowledgeGap>(`${BASE}/${gapId}/resolve`, {
    body: { note },
  });
}

export function dismissKnowledgeGap(
  gapId: string,
  reason: string,
): Promise<KnowledgeGap> {
  return kbApi.post<KnowledgeGap>(`${BASE}/${gapId}/dismiss`, {
    body: { reason },
  });
}

export function reopenKnowledgeGap(gapId: string): Promise<KnowledgeGap> {
  return kbApi.post<KnowledgeGap>(`${BASE}/${gapId}/reopen`);
}
