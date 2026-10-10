import clsx from 'clsx';
import { Lightbulb, Search, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router';
import { loadSpaces, SpaceIcon, useSpaces } from '@entities/space';
import { SidebarToggle } from '@widgets/app-sidebar';
import { SearchResults, useSearch } from '@widgets/search-results';
import { Breadcrumbs } from '@shared/ui/breadcrumbs';
import { Topbar } from '@shared/ui/topbar';
import styles from './SearchPage.module.scss';

const EXAMPLES = [
  'не подключается VPN из дома',
  'как сбросить пароль доменной учётной записи',
  'сроки реакции по критическим инцидентам',
];

export function SearchPage() {
  const [params, setParams] = useSearchParams();
  const urlQuery = params.get('q') ?? '';
  const spaceIds = params.getAll('space');
  const spaces = useSpaces((state) => state.items);
  const [query, setQuery] = useState(urlQuery);
  const [prevUrlQuery, setPrevUrlQuery] = useState(urlQuery);
  const state = useSearch(query, spaceIds);

  useEffect(() => {
    void loadSpaces();
  }, []);

  // Запрос живёт в адресе: ссылкой на поиск можно поделиться
  if (prevUrlQuery !== urlQuery) {
    setPrevUrlQuery(urlQuery);
    setQuery(urlQuery);
  }

  const updateParams = (next: { q?: string; spaces?: string[] }) => {
    const search = new URLSearchParams();
    const q = (next.q ?? query).trim();
    if (q) search.set('q', q);
    (next.spaces ?? spaceIds).forEach((id) => search.append('space', id));
    setParams(search, { replace: true });
  };

  const toggleSpace = (spaceId: string) =>
    updateParams({
      spaces: spaceIds.includes(spaceId)
        ? spaceIds.filter((id) => id !== spaceId)
        : [...spaceIds, spaceId],
    });

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
            updateParams({ q: query });
          }}
        >
          <Search size={18} className={styles.searchIcon} aria-hidden />
          <input
            className={styles.input}
            value={query}
            placeholder="Опишите вопрос или проблему"
            aria-label="Поисковый запрос"
            autoFocus
            onChange={(event) => setQuery(event.target.value)}
            onBlur={() => updateParams({ q: query })}
          />
          {query && (
            <button
              type="button"
              className={styles.clear}
              aria-label="Очистить"
              onClick={() => {
                setQuery('');
                updateParams({ q: '' });
              }}
            >
              <X size={16} aria-hidden />
            </button>
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
                      updateParams({ q: example });
                    }}
                  >
                    {example}
                  </button>
                ))}
              </div>
            </section>
          ) : (
            <SearchResults state={state} query={query} spaces={spaces} />
          )}
        </div>
      </div>
    </>
  );
}
