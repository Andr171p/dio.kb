import { useEffect, useState } from 'react';
import { isAbortError } from '@shared/api';
import { useDebouncedValue } from '@shared/lib/hooks';
import { suggestArticles, type SearchSuggestion } from './suggestions';

type Response =
  | { key: string; items: SearchSuggestion[] }
  | { key: string; error: true };

/** Debounce 200 мс + AbortController — как в спецификации Quick Search. */
export function useSuggestions(
  query: string,
  spaceIds: string[] = [],
  enabled = true,
) {
  const trimmed = query.trim();
  const debounced = useDebouncedValue(trimmed, 200);
  const spacesKey = spaceIds.join(',');
  const key = `${debounced}\n${spacesKey}`;
  const [response, setResponse] = useState<Response | null>(null);

  useEffect(() => {
    if (!enabled || debounced.length < 2) return;
    const controller = new AbortController();

    void suggestArticles(debounced, {
      spaceIds: spacesKey ? spacesKey.split(',') : undefined,
      signal: controller.signal,
    })
      .then((items) => setResponse({ key, items }))
      .catch((error: unknown) => {
        if (!isAbortError(error)) setResponse({ key, error: true });
      });

    return () => controller.abort();
  }, [debounced, spacesKey, key, enabled]);

  if (!enabled || trimmed.length < 2) {
    return { status: 'idle' as const, items: [] as SearchSuggestion[] };
  }
  if (debounced.length < 2 || response?.key !== key) {
    return {
      status: 'loading' as const,
      items:
        response && 'items' in response ? response.items : ([] as SearchSuggestion[]),
    };
  }
  if ('error' in response) {
    return { status: 'error' as const, items: [] as SearchSuggestion[] };
  }
  return { status: 'ready' as const, items: response.items };
}
