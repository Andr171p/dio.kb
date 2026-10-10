import { create } from 'zustand';
import { describeError, kbApi } from '@shared/api';
import { registerStoreReset } from '@shared/lib/store-reset';
import type { ArticleSummary } from './types';

interface SpaceArticlesEntry {
  status: 'loading' | 'ready' | 'error';
  items: ArticleSummary[];
  error: string | null;
}

interface SpaceArticlesState {
  bySpace: Record<string, SpaceArticlesEntry | undefined>;
}

export const useSpaceArticles = create<SpaceArticlesState>()(() => ({
  bySpace: {},
}));

registerStoreReset(() =>
  useSpaceArticles.setState(useSpaceArticles.getInitialState(), true),
);

const pending = new Map<string, Promise<void>>();

function patch(spaceId: string, entry: Partial<SpaceArticlesEntry>) {
  useSpaceArticles.setState(({ bySpace }) => ({
    bySpace: {
      ...bySpace,
      [spaceId]: {
        status: 'loading',
        items: [],
        error: null,
        ...bySpace[spaceId],
        ...entry,
      },
    },
  }));
}

/** Статьи пространства (черновики backend отдаёт только при праве WRITE). */
export function loadSpaceArticles(
  spaceId: string,
  { force = false } = {},
): Promise<void> {
  const current = useSpaceArticles.getState().bySpace[spaceId];
  if (!force && current?.status === 'ready') return Promise.resolve();

  const existing = pending.get(spaceId);
  if (existing) return existing;

  if (!current) patch(spaceId, { status: 'loading' });

  const request = kbApi
    .get<ArticleSummary[]>(`/api/user/v1/spaces/${spaceId}/articles`)
    .then((items) => patch(spaceId, { status: 'ready', items, error: null }))
    .catch((error: unknown) =>
      patch(spaceId, { status: 'error', error: describeError(error) }),
    )
    .finally(() => pending.delete(spaceId));

  pending.set(spaceId, request);
  return request;
}

export function refreshSpaceArticles(spaceId: string): Promise<void> {
  return loadSpaceArticles(spaceId, { force: true });
}
