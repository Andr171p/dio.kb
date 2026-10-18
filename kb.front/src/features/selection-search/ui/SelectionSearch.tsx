import { ArrowRight } from 'lucide-react';
import { useEffect, useRef, useState, type RefObject } from 'react';
import { createPortal } from 'react-dom';
import { Link } from 'react-router';
import {
  markdownToSnippet,
  searchArticles,
  type SearchResult,
} from '@entities/search';
import { useSpaces } from '@entities/space';
import { isAbortError } from '@shared/api';
import { routes } from '@shared/config/routes';
import { Skeleton } from '@shared/ui/skeleton';
import styles from './SelectionSearch.module.scss';

const MIN_LENGTH = 3;
const MAX_LENGTH = 80;
const SHOW_DELAY_MS = 350;
const GAP = 10;

interface Selection {
  text: string;
  rect: DOMRect;
}

type Lookup =
  | { status: 'loading' }
  | { status: 'ready'; result: SearchResult | null }
  | { status: 'error' };

type Response =
  | { query: string; result: SearchResult | null }
  | { query: string; error: true };

/** Короткое выделение внутри контейнера — кандидат для поиска по базе. */
function readSelection(container: HTMLElement): Selection | null {
  const selection = window.getSelection();
  if (!selection || selection.isCollapsed || selection.rangeCount === 0)
    return null;
  const range = selection.getRangeAt(0);
  if (!container.contains(range.commonAncestorContainer)) return null;

  const text = selection.toString().replace(/\s+/g, ' ').trim();
  if (text.length < MIN_LENGTH || text.length > MAX_LENGTH) return null;
  return { text, rect: range.getBoundingClientRect() };
}

interface SelectionSearchProps {
  /** Текст статьи, в котором отслеживается выделение */
  containerRef: RefObject<HTMLElement | null>;
  /** Текущая статья: её саму в подсказке не показываем */
  articleId: string;
}

/**
 * Поиск по выделению: подсказка с лучшим совпадением из базы знаний.
 * Выдача — та же, что в поиске, с проверкой прав на backend.
 */
export function SelectionSearch({
  containerRef,
  articleId,
}: SelectionSearchProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [response, setResponse] = useState<Response | null>(null);
  const spaces = useSpaces((state) => state.items);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;

    const update = () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        const container = containerRef.current;
        setSelection(container ? readSelection(container) : null);
      }, SHOW_DELAY_MS);
    };
    const close = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setSelection(null);
    };
    const hideOnScroll = () => setSelection(null);

    document.addEventListener('selectionchange', update);
    document.addEventListener('keydown', close);
    window.addEventListener('scroll', hideOnScroll, { passive: true });
    return () => {
      clearTimeout(timer);
      document.removeEventListener('selectionchange', update);
      document.removeEventListener('keydown', close);
      window.removeEventListener('scroll', hideOnScroll);
    };
  }, [containerRef]);

  const query = selection?.text;

  useEffect(() => {
    if (!query) return;
    const controller = new AbortController();
    searchArticles({ query, limit: 3 }, controller.signal)
      .then((items) =>
        setResponse({
          query,
          result: items.find((item) => item.article.id !== articleId) ?? null,
        }),
      )
      .catch((error: unknown) => {
        if (!isAbortError(error)) setResponse({ query, error: true });
      });
    return () => controller.abort();
  }, [query, articleId]);

  const lookup: Lookup =
    !response || response.query !== query
      ? { status: 'loading' }
      : 'error' in response
        ? { status: 'error' }
        : { status: 'ready', result: response.result };

  // Карточка в top layer: над текстом, не сдвигая его.
  // Пересчитываем и после ответа — высота карточки меняется
  useEffect(() => {
    const card = cardRef.current;
    if (!card) return;
    if (!selection) {
      if (card.matches(':popover-open')) card.hidePopover();
      return;
    }
    if (!card.matches(':popover-open')) card.showPopover();
    const { rect } = selection;
    const width = card.offsetWidth;
    const viewport = document.documentElement.clientWidth;
    const left = Math.min(Math.max(rect.left, 8), viewport - width - 8);
    card.style.left = `${left}px`;
    card.style.top = `${rect.bottom + GAP}px`;
  }, [selection, response]);

  const result = lookup.status === 'ready' ? lookup.result : null;
  const fragment = result?.fragments[0];
  const spaceName = spaces.find(
    (space) => space.id === result?.article.spaceId,
  )?.name;

  return createPortal(
    <div
      ref={cardRef}
      popover="manual"
      className={styles.card}
      role="dialog"
      aria-label="Поиск по выделению"
      // Клик по карточке не должен снимать выделение и закрывать её
      onMouseDown={(event) => event.preventDefault()}
    >
      {selection && (
        <>
          <p className={styles.term}>{selection.text}</p>
          {lookup.status === 'loading' && (
            <div className={styles.loading}>
              <Skeleton height={10} width="90%" />
              <Skeleton height={10} width="70%" />
            </div>
          )}
          {lookup.status === 'error' && (
            <p className={styles.text}>Не удалось выполнить поиск.</p>
          )}
          {lookup.status === 'ready' &&
            (result ? (
              <>
                <Link
                  to={routes.article(result.article.id, fragment?.anchor)}
                  className={styles.article}
                  onClick={() => setSelection(null)}
                >
                  {result.article.title}
                </Link>
                {fragment && (
                  <p className={styles.text}>
                    {markdownToSnippet(fragment.text, 160)}
                  </p>
                )}
                {spaceName && (
                  <p className={styles.source}>Источник: {spaceName}</p>
                )}
              </>
            ) : (
              <p className={styles.text}>
                В других статьях совпадений не нашлось.
              </p>
            ))}
          <Link
            to={routes.search(selection.text)}
            className={styles.more}
            onClick={() => setSelection(null)}
          >
            Найти в базе <ArrowRight size={13} aria-hidden />
          </Link>
        </>
      )}
    </div>,
    document.body,
  );
}
