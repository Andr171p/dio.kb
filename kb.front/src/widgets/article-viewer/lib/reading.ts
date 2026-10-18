import { articleIdFromHref } from '@shared/config/routes';

/** Скорость чтения инструкций на русском, слов в минуту */
const WORDS_PER_MINUTE = 180;

/** Время чтения в минутах (минимум одна): блоки кода и ссылки считаются как текст. */
export function readingMinutes(markdown: string): number {
  const words = markdown
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\]\([^)]*\)/g, ']')
    .split(/[^\p{L}\p{N}]+/u)
    .filter(Boolean).length;
  return Math.max(1, Math.round(words / WORDS_PER_MINUTE));
}

export interface RelatedArticle {
  id: string;
  title: string;
}

const LINK = /(?<!!)\[([^\]]+)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g;

/**
 * Статьи базы, на которые ссылается текст, — «Связанные материалы».
 * Берём только то, что уже есть в статье, поэтому ничего недоступного не раскрываем.
 */
export function relatedArticles(
  markdown: string,
  currentId: string,
  limit = 5,
): RelatedArticle[] {
  const seen = new Set<string>([currentId]);
  const result: RelatedArticle[] = [];

  for (const [, text, href] of markdown.matchAll(LINK)) {
    const id = articleIdFromHref(href);
    if (!id || seen.has(id)) continue;
    seen.add(id);
    result.push({ id, title: text.replace(/[*_`]/g, '').trim() });
    if (result.length === limit) break;
  }
  return result;
}
