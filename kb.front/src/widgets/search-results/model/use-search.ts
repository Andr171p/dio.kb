import { useEffect, useState } from 'react';
import { searchArticles, type SearchResult } from '@entities/search';
import { describeError, isAbortError } from '@shared/api';
import { useDebouncedValue } from '@shared/lib/hooks';

export type SearchState =
  | { status: 'idle' }
  | { status: 'loading'; previous: SearchResult[] | null }
  | { status: 'ready'; items: SearchResult[] }
  | { status: 'error'; error: string };

type Response =
  { key: string; items: SearchResult[] } | { key: string; error: string };

const LIMIT = 20;

/** Поиск с задержкой ввода и отменой устаревших запросов. */
export function useSearch(query: string, spaceIds: string[]): SearchState {
  const debounced = useDebouncedValue(query.trim(), 400);
  const spacesKey = spaceIds.join(',');
  const key = `${debounced}\n${spacesKey}`;
  // Ответ хранится вместе с запросом: «загрузка» — это ответ на другой запрос
  const [response, setResponse] = useState<Response | null>(null);

  useEffect(() => {
    if (!debounced) return;
    const controller = new AbortController();

    searchArticles(
      {
        query: debounced,
        spaceIds: spacesKey ? spacesKey.split(',') : undefined,
        limit: LIMIT,
      },
      controller.signal,
    )
      .then((items) => setResponse({ key, items }))
      .catch((error: unknown) => {
        if (!isAbortError(error))
          setResponse({ key, error: describeError(error) });
      });

    return () => controller.abort();
  }, [debounced, spacesKey, key]);

  if (!debounced) return { status: 'idle' };
  if (response?.key !== key)
    return {
      status: 'loading',
      previous: response && 'items' in response ? response.items : null,
    };
  return 'items' in response
    ? { status: 'ready', items: response.items }
    : { status: 'error', error: response.error };
}
