import { ArrowRight } from 'lucide-react';
import type { ReactNode } from 'react';
import { Link } from 'react-router';
import { markdownToSnippet, type SearchResult } from '@entities/search';
import type { Space } from '@entities/space';
import { routes } from '@shared/config/routes';
import { pluralize } from '@shared/lib/format';
import { Button } from '@shared/ui/button';
import { EmptyState } from '@shared/ui/empty-state';
import { Skeleton } from '@shared/ui/skeleton';
import type { SearchState } from '../model/use-search';
import styles from './SearchResults.module.scss';

const MIN_TERM_LENGTH = 3;
const SECTION_LINKS_LIMIT = 3;

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/** Подсветка слов запроса во фрагменте (по основе слова — поиск семантический и со стеммингом). */
function highlight(text: string, query: string): ReactNode {
  const stems = query
    .toLocaleLowerCase('ru')
    .split(/[^\p{L}\p{N}]+/u)
    .filter((word) => word.length >= MIN_TERM_LENGTH)
    .map((word) => escapeRegExp(word.length > 5 ? word.slice(0, -2) : word));
  if (stems.length === 0) return text;

  const pattern = new RegExp(`(${stems.join('|')})[\\p{L}\\p{N}]*`, 'giu');
  const parts: ReactNode[] = [];
  let last = 0;
  for (const match of text.matchAll(pattern)) {
    const index = match.index ?? 0;
    parts.push(text.slice(last, index), <mark key={index}>{match[0]}</mark>);
    last = index + match[0].length;
  }
  parts.push(text.slice(last));
  return parts;
}

/** Разделы статьи, где нашлись совпадения: ссылка ведёт прямо к заголовку. */
function sectionLinks(result: SearchResult) {
  const seen = new Set<string>();
  return result.fragments
    .filter((fragment) => fragment.anchor && fragment.headingPath.length > 0)
    .map((fragment) => ({
      anchor: fragment.anchor,
      title: fragment.headingPath[fragment.headingPath.length - 1],
    }))
    .filter(({ anchor }) => {
      if (!anchor || seen.has(anchor)) return false;
      seen.add(anchor);
      return true;
    })
    .slice(0, SECTION_LINKS_LIMIT);
}

function ResultItem({
  result,
  space,
  query,
}: {
  result: SearchResult;
  space: Space | undefined;
  query: string;
}) {
  const { article, fragments } = result;
  const [first] = fragments;
  const sections = sectionLinks(result);
  const path = [space?.name, ...(first?.headingPath.slice(0, -1) ?? [])]
    .filter(Boolean)
    .join(' / ');

  return (
    <li className={styles.result}>
      {path && <p className={styles.path}>{path}</p>}
      <Link
        to={routes.article(article.id, first?.anchor)}
        className={styles.title}
      >
        {article.title}
      </Link>
      {first && (
        <p className={styles.snippet}>
          {highlight(markdownToSnippet(first.text, 240), query)}
        </p>
      )}
      {sections.length > 0 && (
        <ul className={styles.sections}>
          {sections.map((section) => (
            <li key={section.anchor}>
              <Link
                to={routes.article(article.id, section.anchor)}
                className={styles.section}
              >
                {section.title}
                <ArrowRight size={13} aria-hidden />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </li>
  );
}

interface SearchResultsProps {
  state: SearchState;
  query: string;
  spaces: Space[];
  /** Повторить запрос после ошибки */
  onRetry: () => void;
  /** Снять фильтры по пространствам, если они заданы */
  onResetFilters?: () => void;
}

/** Выдача поиска: статьи с лучшими фрагментами. Совпадения одной статьи сгруппированы. */
export function SearchResults({
  state,
  query,
  spaces,
  onRetry,
  onResetFilters,
}: SearchResultsProps) {
  const spaceById = new Map(spaces.map((space) => [space.id, space]));

  if (state.status === 'error')
    return (
      <EmptyState
        title="Не удалось загрузить результаты"
        description="Запрос сохранён. Проверьте подключение и повторите попытку."
        action={<Button onClick={onRetry}>Повторить поиск</Button>}
      />
    );

  const items =
    state.status === 'ready'
      ? state.items
      : state.status === 'loading'
        ? state.previous
        : null;

  if (state.status === 'loading' && !items)
    return (
      <div className={styles.skeletons} aria-busy>
        <Skeleton height={10} width="40%" />
        <Skeleton height={10} width="70%" />
        <Skeleton height={10} width="55%" />
      </div>
    );

  if (!items) return null;

  if (items.length === 0)
    return (
      <EmptyState
        title={`По запросу «${query.trim()}» нет результатов`}
        description={
          onResetFilters
            ? 'Проверьте формулировку или попробуйте искать во всех пространствах.'
            : 'Проверьте формулировку или опишите вопрос другими словами. Только что опубликованные статьи появляются в поиске через несколько секунд.'
        }
        action={
          onResetFilters && (
            <Button onClick={onResetFilters}>Сбросить фильтры</Button>
          )
        }
      />
    );

  return (
    <div aria-busy={state.status === 'loading'} className={styles.wrapper}>
      <h2 className={styles.count}>
        Найдено {pluralize(items.length, ['статья', 'статьи', 'статей'])}
      </h2>
      <p className={styles.hint}>
        Совпадения из одной статьи собраны вместе. Откройте нужный раздел.
      </p>
      <ul className={styles.list}>
        {items.map((result) => (
          <ResultItem
            key={result.article.id}
            result={result}
            space={spaceById.get(result.article.spaceId)}
            query={query}
          />
        ))}
      </ul>
    </div>
  );
}
