import clsx from 'clsx';
import { FileText, Lightbulb, Search, X } from 'lucide-react';
import { useEffect, useId, useRef, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router';
import { useSuggestions } from '@entities/search';
import { loadSpaces, SpaceIcon, useSpaces } from '@entities/space';
import {
  consumeAnswerAutoStart,
  readAnswerPointer,
  resetAnswerRun,
  restoreAnswerRun,
  startAnswerRun,
  useAnswerRun,
} from '@features/answer-generation';
import { AnswerPanel } from '@widgets/answer-panel';
import { SidebarToggle } from '@widgets/app-sidebar';
import { SearchResults, useSearch } from '@widgets/search-results';
import { routes } from '@shared/config/routes';
import { Breadcrumbs } from '@shared/ui/breadcrumbs';
import { Spinner } from '@shared/ui/spinner';
import { Topbar } from '@shared/ui/topbar';
import styles from './SearchPage.module.scss';

const EXAMPLES = [
  'не подключается VPN из дома',
  'как сбросить пароль доменной учётной записи',
  'сроки реакции по критическим инцидентам',
];

export function SearchPage() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const urlQuery = params.get('q') ?? '';
  const answerId = params.get('answer');
  const spaceIds = params.getAll('space');
  const spaces = useSpaces((state) => state.items);
  const [query, setQuery] = useState(urlQuery);
  const [prevUrlQuery, setPrevUrlQuery] = useState(urlQuery);
  const [suggestOpen, setSuggestOpen] = useState(false);
  const [activeSuggest, setActiveSuggest] = useState(0);
  const state = useSearch(query, spaceIds);
  const suggestions = useSuggestions(query, spaceIds, suggestOpen);
  const answerPhase = useAnswerRun((s) => s.phase);
  const answerQuestion = useAnswerRun((s) => s.question);
  const startedRef = useRef<string | null>(null);
  const listId = useId();

  useEffect(() => {
    void loadSpaces();
  }, []);

  if (prevUrlQuery !== urlQuery) {
    setPrevUrlQuery(urlQuery);
    setQuery(urlQuery);
  }

  useEffect(() => {
    if (!answerId) return;
    if (startedRef.current === answerId) return;
    startedRef.current = answerId;
    void restoreAnswerRun(answerId);
  }, [answerId]);

  // Восстановление ответа после ухода со страницы (sessionStorage + URL)
  useEffect(() => {
    if (answerId) return;
    const pointer = readAnswerPointer();
    if (!pointer) return;
    const q = urlQuery.trim();
    if (q && q !== pointer.question.trim()) return;
    startedRef.current = pointer.answerId;
    setParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.set('answer', pointer.answerId);
        if (!next.get('q') && pointer.question) next.set('q', pointer.question);
        return next;
      },
      { replace: true },
    );
    void restoreAnswerRun(pointer.answerId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (answerId) return;
    const pending =
      consumeAnswerAutoStart() ??
      (params.get('ai') === '1' && urlQuery.trim().length >= 2
        ? { question: urlQuery.trim(), spaceIds }
        : null);
    if (!pending) return;

    const next = new URLSearchParams(params);
    next.delete('ai');
    setParams(next, { replace: true });

    void startAnswerRun(pending).then((id) => {
      if (!id) return;
      startedRef.current = id;
      setParams(
        (prev) => {
          const withAnswer = new URLSearchParams(prev);
          withAnswer.set('answer', id);
          withAnswer.delete('ai');
          return withAnswer;
        },
        { replace: true },
      );
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Новый поисковый запрос не должен держать старый AnswerRun.
  // starting/running не трогаем: q в URL может отстать на тик от askAi.
  useEffect(() => {
    const q = urlQuery.trim();
    if (
      !q ||
      answerPhase === 'idle' ||
      answerPhase === 'starting' ||
      answerPhase === 'running'
    ) {
      return;
    }
    if (!answerQuestion) return;
    if (q === answerQuestion.trim()) return;
    resetAnswerRun();
    startedRef.current = null;
    setParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.delete('answer');
        return next;
      },
      { replace: true },
    );
  }, [urlQuery, answerPhase, answerQuestion, setParams]);

  const updateParams = (next: {
    q?: string;
    spaces?: string[];
    answer?: string | null;
  }) => {
    const search = new URLSearchParams();
    const q = (next.q ?? query).trim();
    if (q) search.set('q', q);
    (next.spaces ?? spaceIds).forEach((id) => search.append('space', id));

    const keepAnswer =
      next.answer === undefined
        ? Boolean(params.get('answer')) &&
          q === (answerQuestion?.trim() ?? q)
        : Boolean(next.answer);
    if (keepAnswer) {
      const id = next.answer ?? params.get('answer');
      if (id) search.set('answer', id);
    } else {
      resetAnswerRun();
      startedRef.current = null;
    }

    setParams(search, { replace: true });
  };

  const toggleSpace = (spaceId: string) =>
    updateParams({
      spaces: spaceIds.includes(spaceId)
        ? spaceIds.filter((id) => id !== spaceId)
        : [...spaceIds, spaceId],
    });

  const clearQuery = () => {
    setQuery('');
    setSuggestOpen(false);
    resetAnswerRun();
    startedRef.current = null;
    updateParams({ q: '', answer: null });
  };

  const commitSearch = (value = query) => {
    setSuggestOpen(false);
    // answer сохраняем, если запрос совпадает с текущим AnswerRun
    updateParams({ q: value });
  };

  const suggestItems = suggestions.items;
  const showSuggest =
    suggestOpen &&
    query.trim().length >= 2 &&
    (suggestions.status === 'loading' || suggestItems.length > 0);

  return (
    <>
      <Topbar
        start={
          <>
            <SidebarToggle />
            <Breadcrumbs items={[{ label: 'Поиск по содержимому' }]} />
          </>
        }
      />
      <div className={styles.page}>
        <form
          className={styles.search}
          role="search"
          onSubmit={(event) => {
            event.preventDefault();
            const selected = showSuggest ? suggestItems[activeSuggest] : null;
            if (selected) {
              setSuggestOpen(false);
              void navigate(routes.article(selected.articleId));
              return;
            }
            commitSearch();
          }}
        >
          <Search size={18} className={styles.searchIcon} aria-hidden />
          <input
            className={styles.input}
            value={query}
            placeholder="Опишите вопрос или проблему"
            aria-label="Поисковый запрос"
            aria-autocomplete="list"
            aria-controls={listId}
            aria-expanded={showSuggest}
            autoFocus
            onChange={(event) => {
              setQuery(event.target.value);
              setSuggestOpen(true);
              setActiveSuggest(0);
            }}
            onFocus={() => setSuggestOpen(true)}
            onBlur={() => {
              // Даём клику по подсказке сработать
              window.setTimeout(() => setSuggestOpen(false), 120);
              const trimmed = query.trim();
              if (trimmed !== urlQuery.trim()) commitSearch(trimmed);
            }}
            onKeyDown={(event) => {
              if (!showSuggest || suggestItems.length === 0) return;
              if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
                event.preventDefault();
                const delta = event.key === 'ArrowDown' ? 1 : -1;
                setActiveSuggest(
                  (activeSuggest + delta + suggestItems.length) %
                    suggestItems.length,
                );
              } else if (event.key === 'Escape') {
                setSuggestOpen(false);
              }
            }}
          />
          {query && (
            <button
              type="button"
              className={styles.clear}
              aria-label="Очистить"
              onClick={clearQuery}
            >
              <X size={16} aria-hidden />
            </button>
          )}

          {showSuggest && (
            <ul id={listId} role="listbox" className={styles.suggest}>
              {suggestions.status === 'loading' && suggestItems.length === 0 && (
                <li className={styles.suggestStatus}>
                  <Spinner size={14} /> Подсказки…
                </li>
              )}
              {suggestItems.map((item, index) => (
                <li key={item.articleId} role="option" aria-selected={index === activeSuggest}>
                  <Link
                    to={routes.article(item.articleId)}
                    className={clsx(
                      styles.suggestItem,
                      index === activeSuggest && styles.suggestActive,
                    )}
                    onMouseDown={(event) => event.preventDefault()}
                    onPointerMove={() => setActiveSuggest(index)}
                  >
                    <FileText size={15} aria-hidden />
                    <span>{item.title}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </form>

        {spaces.length > 1 && (
          <div
            className={styles.filters}
            role="group"
            aria-label="Пространства"
          >
            {spaces.map((space) => {
              const active = spaceIds.includes(space.id);
              return (
                <button
                  key={space.id}
                  type="button"
                  aria-pressed={active}
                  className={clsx(styles.chip, active && styles.chipActive)}
                  onClick={() => toggleSpace(space.id)}
                >
                  <SpaceIcon spaceKey={space.key} />
                  {space.name}
                </button>
              );
            })}
          </div>
        )}

        <div className={styles.workspace}>
          {(query.trim().length >= 2 || answerPhase !== 'idle') && (
            <AnswerPanel
              query={query}
              spaceIds={spaceIds}
              onAnswerIdChange={(id) => {
                startedRef.current = id;
              }}
            />
          )}

          <div className={styles.results}>
            {state.status === 'idle' ? (
              <section className={styles.tips}>
                <p className={styles.tipsTitle}>
                  <Lightbulb size={16} aria-hidden /> Поиск понимает смысл, а не
                  только слова
                </p>
                <p className={styles.tipsText}>
                  Опишите ситуацию так, как написали бы коллеге. Например:
                </p>
                <div className={styles.examples}>
                  {EXAMPLES.map((example) => (
                    <button
                      key={example}
                      type="button"
                      className={styles.example}
                      onClick={() => {
                        setQuery(example);
                        commitSearch(example);
                      }}
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </section>
            ) : (
              <>
                <h2 className={styles.resultsTitle}>Результаты поиска</h2>
                <SearchResults state={state} query={query} spaces={spaces} />
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
