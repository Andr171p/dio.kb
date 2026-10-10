import { create } from 'zustand';
import { ApiError, describeError, kbApi } from '@shared/api';
import { registerStoreReset } from '@shared/lib/store-reset';
import type { ArticleDetail, ArticleVersion } from './types';

export interface ArticleEntry {
  status: 'loading' | 'ready' | 'error';
  data: ArticleDetail | null;
  error: string | null;
  /** HTTP-статус ошибки: 404 и 403 показываем как «не найдено» */
  errorStatus: number | null;
}

interface ArticlesState {
  entries: Record<string, ArticleEntry | undefined>;
}

export const useArticles = create<ArticlesState>()(() => ({ entries: {} }));

registerStoreReset(() =>
  useArticles.setState(useArticles.getInitialState(), true),
);

const key = (articleId: string, version: ArticleVersion) =>
  `${articleId}:${version}`;

const PATHS: Record<ArticleVersion, (id: string) => string> = {
  published: (id) => `/api/user/v1/articles/${id}`,
  draft: (id) => `/api/user/v1/articles/${id}/draft`,
};

function patch(entryKey: string, entry: Partial<ArticleEntry>) {
  useArticles.setState(({ entries }) => ({
    entries: {
      ...entries,
      [entryKey]: {
        status: 'loading',
        data: null,
        error: null,
        errorStatus: null,
        ...entries[entryKey],
        ...entry,
      },
    },
  }));
}

const pending = new Map<string, Promise<ArticleDetail | null>>();

export function loadArticle(
  articleId: string,
  version: ArticleVersion,
): Promise<ArticleDetail | null> {
  const entryKey = key(articleId, version);
  const existing = pending.get(entryKey);
  if (existing) return existing;

  if (!useArticles.getState().entries[entryKey]?.data)
    patch(entryKey, { status: 'loading', error: null, errorStatus: null });

  const request = kbApi
    .get<ArticleDetail>(PATHS[version](articleId))
    .then((data) => {
      patch(entryKey, {
        status: 'ready',
        data,
        error: null,
        errorStatus: null,
      });
      return data;
    })
    .catch((error: unknown) => {
      // Недоступная статья не должна остаться в кеше
      patch(entryKey, {
        status: 'error',
        data: null,
        error: describeError(error),
        errorStatus: error instanceof ApiError ? error.status : null,
      });
      return null;
    })
    .finally(() => pending.delete(entryKey));

  pending.set(entryKey, request);
  return request;
}

/** Кладёт свежий ответ мутации (новая редакция, публикация) в кеш. */
export function setArticleDetail(
  detail: ArticleDetail,
  version: ArticleVersion,
) {
  patch(key(detail.article.id, version), {
    status: 'ready',
    data: detail,
    error: null,
    errorStatus: null,
  });
}

/** После публикации/архивации версии в кеше устарели. */
export function invalidateArticle(articleId: string) {
  useArticles.setState(({ entries }) => {
    const next = { ...entries };
    delete next[key(articleId, 'published')];
    delete next[key(articleId, 'draft')];
    return { entries: next };
  });
}

export function useArticleEntry(
  articleId: string | undefined,
  version: ArticleVersion,
): ArticleEntry | undefined {
  return useArticles((state) =>
    articleId ? state.entries[key(articleId, version)] : undefined,
  );
}
