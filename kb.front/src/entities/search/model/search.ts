import { kbApi } from '@shared/api';
import type { SearchQuery, SearchResult } from './types';

/**
 * Поиск по опубликованным статьям. Backend сам ограничивает выдачу правами пользователя
 * и повторно проверяет доступ — клиент ничего не фильтрует.
 */
export async function searchArticles(
  { query, spaceIds, limit = 10 }: SearchQuery,
  signal?: AbortSignal,
): Promise<SearchResult[]> {
  const { items } = await kbApi.post<{ items: SearchResult[] }>(
    '/api/user/v1/search',
    {
      body: { query, spaceIds: spaceIds?.length ? spaceIds : undefined, limit },
      signal,
    },
  );
  return items;
}
