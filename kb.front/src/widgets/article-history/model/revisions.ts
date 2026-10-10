import { useEffect, useState } from 'react';
import type {
  ArticleRevision,
  ArticleRevisionSummary,
} from '@entities/article';
import { describeError, isAbortError, kbApi } from '@shared/api';

type Loadable<T> =
  | { status: 'loading' }
  | { status: 'ready'; data: T }
  | { status: 'error'; error: string };

/** История редакций статьи (новые сверху). Требует права WRITE — иначе backend вернёт 403. */
export function useRevisionList(
  articleId: string,
  reloadKey: string | undefined,
) {
  const [state, setState] = useState<Loadable<ArticleRevisionSummary[]>>({
    status: 'loading',
  });

  useEffect(() => {
    const controller = new AbortController();
    kbApi
      .get<ArticleRevisionSummary[]>(
        `/api/user/v1/articles/${articleId}/revisions`,
        {
          signal: controller.signal,
        },
      )
      .then((data) =>
        setState({
          status: 'ready',
          data: [...data].sort((a, b) => b.number - a.number),
        }),
      )
      .catch((error: unknown) => {
        if (!isAbortError(error))
          setState({ status: 'error', error: describeError(error) });
      });
    return () => controller.abort();
  }, [articleId, reloadKey]);

  return state;
}

/** Содержимое редакций: неизменяемы, поэтому кешируем навсегда в пределах экрана. */
const revisionCache = new Map<string, Promise<ArticleRevision>>();

function fetchRevision(
  articleId: string,
  revisionId: string,
): Promise<ArticleRevision> {
  const cached = revisionCache.get(revisionId);
  if (cached) return cached;
  const request = kbApi.get<ArticleRevision>(
    `/api/user/v1/articles/${articleId}/revisions/${revisionId}`,
  );
  revisionCache.set(revisionId, request);
  request.catch(() => revisionCache.delete(revisionId));
  return request;
}

export function useRevisions(
  articleId: string,
  revisionIds: (string | null | undefined)[],
) {
  const key = revisionIds.join(',');
  // Результат хранится с ключом запроса: ответ на прежний выбор — это «загрузка» нового
  const [result, setResult] = useState<{
    key: string;
    state: Loadable<(ArticleRevision | null)[]>;
  }>();

  useEffect(() => {
    let cancelled = false;
    Promise.all(
      key
        .split(',')
        .map((id) =>
          id ? fetchRevision(articleId, id) : Promise.resolve(null),
        ),
    )
      .then(
        (data) =>
          !cancelled && setResult({ key, state: { status: 'ready', data } }),
      )
      .catch(
        (error: unknown) =>
          !cancelled &&
          setResult({
            key,
            state: { status: 'error', error: describeError(error) },
          }),
      );
    return () => {
      cancelled = true;
    };
  }, [articleId, key]);

  return result?.key === key ? result.state : ({ status: 'loading' } as const);
}
