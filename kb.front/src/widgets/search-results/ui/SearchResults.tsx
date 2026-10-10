import { ChevronRight, FileText, SearchX } from 'lucide-react';
import { Fragment, type ReactNode } from 'react';
import { Link } from 'react-router';
import { markdownToSnippet, type SearchResult } from '@entities/search';
import type { Space } from '@entities/space';
import { routes } from '@shared/config/routes';
import { formatShortDate } from '@shared/lib/format';
import { EmptyState } from '@shared/ui/empty-state';
import { Notice } from '@shared/ui/notice';
import { Skeleton } from '@shared/ui/skeleton';
import type { SearchState } from '../model/use-search';
import styles from './SearchResults.module.scss';

const MIN_TERM_LENGTH = 3;

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

function ResultCard({
  result,
  space,
  query,
}: {
  result: SearchResult;
  space: Space | undefined;
  query: string;
}) {
  const { article, fragments } = result;
  const firstAnchor = fragments[0]?.anchor;

  return (
    <li className={styles.result}>
      <Link
        to={routes.article(article.id, firstAnchor)}
        className={styles.titleLink}
      >
        <FileText size={16} className={styles.titleIcon} aria-hidden />
        <span className={styles.title}>{article.title}</span>
      </Link>
      <div className={styles.meta}>
        {space && <span>{space.name}</span>}
        <span aria-hidden>·</span>
        <span>опубликовано {formatShortDate(article.publishedAt)}</span>
      </div>
      <ul className={styles.fragments}>
        {fragments.map((fragment) => (
          <li key={fragment.chunkId}>
            <Link
              to={routes.article(article.id, fragment.anchor)}
              className={styles.fragment}
            >
              {fragment.headingPath.length > 0 && (
                <span className={styles.path}>
                  {fragment.headingPath.map((heading, index) => (
                    <Fragment key={index}>
                      {index > 0 && <ChevronRight size={12} aria-hidden />}
                      <span>{heading}</span>
                    </Fragment>
                  ))}
                </span>
              )}
              <span className={styles.snippet}>
                {highlight(markdownToSnippet(fragment.text, 280), query)}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </li>
  );
}

interface SearchResultsProps {
  state: SearchState;
  query: string;
  spaces: Space[];
}

/** Выдача поиска: статьи с лучшими фрагментами. Простые поверхности — без визуального шума. */
export function SearchResults({ state, query, spaces }: SearchResultsProps) {
  const spaceById = new Map(spaces.map((space) => [space.id, space]));

  if (state.status === 'error') return <Notice>{state.error}</Notice>;

  const items =
    state.status === 'ready'
      ? state.items
      : state.status === 'loading'
        ? state.previous
        : null;

  if (state.status === 'loading' && !items)
    return (
      <div className={styles.skeletons} aria-busy>
        {[0, 1, 2].map((index) => (
          <div key={index} className={styles.skeleton}>
            <Skeleton height={18} width="45%" />
            <Skeleton height={12} width="25%" />
            <Skeleton height={44} />
          </div>
        ))}
      </div>
    );

  if (!items) return null;

  if (items.length === 0)
    return (
      <EmptyState
        icon={SearchX}
        title="Ничего не найдено"
        description="Попробуйте описать проблему другими словами или убрать фильтр по пространствам. Только что опубликованные статьи появляются в поиске через несколько секунд."
      />
    );

  return (
    <div aria-busy={state.status === 'loading'} className={styles.wrapper}>
      <p className={styles.count}>Найдено статей: {items.length}</p>
      <ul className={styles.list}>
        {items.map((result) => (
          <ResultCard
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
