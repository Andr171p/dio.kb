import { kbApi } from '@shared/api';

export interface SearchSuggestion {
  articleId: string;
  spaceId: string;
  slug: string;
  title: string;
}

/** Подсказки по заголовкам (PostgreSQL autocomplete, без LLM). */
export async function suggestArticles(
  query: string,
  options?: { spaceIds?: string[]; limit?: number; signal?: AbortSignal },
): Promise<SearchSuggestion[]> {
  const trimmed = query.trim();
  if (trimmed.length < 2) return [];

  const { items } = await kbApi.post<{ items: SearchSuggestion[] }>(
    '/api/user/v1/search/suggestions',
    {
      body: {
        query: trimmed,
        spaceIds: options?.spaceIds?.length ? options.spaceIds : undefined,
        limit: options?.limit ?? 6,
      },
      signal: options?.signal,
    },
  );
  return items;
}
