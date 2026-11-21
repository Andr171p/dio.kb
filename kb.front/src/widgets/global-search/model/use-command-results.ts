import { useEffect, useMemo, useState } from 'react';
import {
  loadSpaceArticles,
  useSpaceArticles,
  type ArticleSummary,
} from '@entities/article';
import {
  markdownToSnippet,
  searchArticles,
  suggestArticles,
  type SearchSuggestion,
} from '@entities/search';
import { useSpaces } from '@entities/space';
import { isAbortError } from '@shared/api';
import { useDebouncedValue } from '@shared/lib/hooks';
import { useRecentArticles } from './recent-store';

export interface CommandArticle {
  id: string;
  title: string;
  spaceId: string;
  /** Путь заголовков и фрагмент — для результатов по содержимому */
  headingPath?: string[];
  snippet?: string;
  anchor?: string | null;
  status?: ArticleSummary['status'];
}

const TITLE_LIMIT = 6;
const CONTENT_LIMIT = 5;
const MIN_CONTENT_QUERY = 2;

function normalize(value: string): string {
  return value.toLocaleLowerCase('ru').replace(/ё/g, 'е');
}

/**
 * Результаты палитры: мгновенный поиск по заголовкам уже доступных статей
 * и семантический поиск по содержимому через Knowledge API.
 */
export function useCommandResults(query: string, open: boolean) {
  const spaces = useSpaces((state) => state.items);
  const bySpace = useSpaceArticles((state) => state.bySpace);
  const recent = useRecentArticles((state) => state.items);
  const trimmed = query.trim();
  const debounced = useDebouncedValue(trimmed, 250);

  const [content, setContent] = useState<{
    query: string;
    items: CommandArticle[];
    status: 'idle' | 'loading' | 'ready' | 'error';
  }>({ query: '', items: [], status: 'idle' });

  const [suggestions, setSuggestions] = useState<{
    query: string;
    items: SearchSuggestion[];
  }>({ query: '', items: [] });

  // Локальные статьи — мгновенный fallback, пока едут подсказки с API
  useEffect(() => {
    if (!open) return;
    spaces.forEach((space) => void loadSpaceArticles(space.id));
  }, [open, spaces]);

  useEffect(() => {
    if (!open || debounced.length < MIN_CONTENT_QUERY) return;
    const controller = new AbortController();

    void suggestArticles(debounced, {
      limit: TITLE_LIMIT,
      signal: controller.signal,
    })
      .then((items) => setSuggestions({ query: debounced, items }))
      .catch((error: unknown) => {
        if (!isAbortError(error)) setSuggestions({ query: debounced, items: [] });
      });

    return () => controller.abort();
  }, [debounced, open]);

  const localTitleMatches = useMemo<CommandArticle[]>(() => {
    if (!trimmed) return [];
    const needle = normalize(trimmed);
    const all = spaces.flatMap((space) => bySpace[space.id]?.items ?? []);

    return (
      all
        .filter((article) => article.status !== 'archived')
        .map((article) => ({
          article,
          index: normalize(article.title).indexOf(needle),
        }))
        .filter(({ index }) => index >= 0)
        .sort(
          (a, b) =>
            a.index - b.index ||
            a.article.title.localeCompare(b.article.title, 'ru'),
        )
        .slice(0, TITLE_LIMIT)
        .map(({ article }) => ({
          id: article.id,
          title: article.title,
          spaceId: article.spaceId,
          status: article.status,
        }))
    );
  }, [trimmed, spaces, bySpace]);

  const titleMatches =
    suggestions.query === debounced && suggestions.items.length > 0
      ? suggestions.items.map((item) => ({
          id: item.articleId,
          title: item.title,
          spaceId: item.spaceId,
        }))
      : localTitleMatches;

  useEffect(() => {
    if (!open || debounced.length < MIN_CONTENT_QUERY) return;
    const controller = new AbortController();

    searchArticles(
      { query: debounced, limit: CONTENT_LIMIT },
      controller.signal,
    )
      .then((results) =>
        setContent({
          query: debounced,
          status: 'ready',
          items: results.map(({ article, fragments }) => {
            const fragment = fragments[0];
            return {
              id: article.id,
              title: article.title,
              spaceId: article.spaceId,
              headingPath: fragment?.headingPath,
              snippet: fragment
                ? markdownToSnippet(fragment.text, 160)
                : undefined,
              anchor: fragment?.anchor,
            };
          }),
        }),
      )
      .catch((error: unknown) => {
        if (!isAbortError(error))
          setContent({ query: debounced, items: [], status: 'error' });
      });

    return () => controller.abort();
  }, [debounced, open]);

  const titleIds = new Set(titleMatches.map((item) => item.id));
  const fresh = content.query === debounced;
  const contentMatches = fresh
    ? content.items.filter((item) => !titleIds.has(item.id))
    : [];

  return {
    recent: trimmed ? [] : recent,
    titleMatches,
    contentMatches,
    contentStatus:
      trimmed.length < MIN_CONTENT_QUERY
        ? 'idle'
        : debounced !== trimmed || !fresh
          ? 'loading'
          : content.status,
  } as const;
}
