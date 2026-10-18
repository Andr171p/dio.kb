import { X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router';
import { loadSpaces, useSpaces } from '@entities/space';
import { AppHeader } from '@widgets/app-shell';
import { SearchResults, useSearch } from '@widgets/search-results';
import { MOD_KEY_LABEL } from '@shared/lib/hooks';
import { Chip, ChipGroup } from '@shared/ui/chip';
import { SearchField } from '@shared/ui/search-field';
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
  const [state, retry] = useSearch(query, spaceIds);

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

  const resetFilters = () => updateParams({ spaces: [] });

  return (
    <>
      <AppHeader crumbs={[{ label: 'Поиск по базе знаний' }]} />
      <div className={styles.page}>
        <form
          role="search"
          onSubmit={(event) => {
            event.preventDefault();
            updateParams({ q: query });
          }}
        >
          <SearchField
            value={query}
            placeholder="Опишите вопрос или проблему"
            aria-label="Поисковый запрос"
            autoFocus
            shortcut={query ? undefined : [MOD_KEY_LABEL, 'K']}
            trailing={
              query && (
                <button
                  type="button"
                  className={styles.clear}
                  aria-label="Очистить"
                  onClick={() => {
                    setQuery('');
                    updateParams({ q: '' });
                  }}
                >
                  <X size={18} aria-hidden />
                </button>
              )
            }
            onChange={(event) => setQuery(event.target.value)}
            onBlur={() => updateParams({ q: query })}
          />
        </form>

        {spaces.length > 1 && (
          <ChipGroup className={styles.filters} aria-label="Пространства">
            <Chip selected={spaceIds.length === 0} onClick={resetFilters}>
              Все пространства
            </Chip>
            {spaces.map((space) => (
              <Chip
                key={space.id}
                selected={spaceIds.includes(space.id)}
                onClick={() => toggleSpace(space.id)}
              >
                {space.name}
              </Chip>
            ))}
            {spaceIds.length > 0 && (
              <Chip onClick={resetFilters}>Сбросить</Chip>
            )}
          </ChipGroup>
        )}

        <div className={styles.results}>
          {state.status === 'idle' ? (
            <section className={styles.tips}>
              <h2 className={styles.tipsTitle}>
                Поиск понимает смысл, а не только слова
              </h2>
              <p className={styles.tipsText}>
                Опишите ситуацию так, как написали бы коллеге. Например:
              </p>
              <ChipGroup className={styles.examples}>
                {EXAMPLES.map((example) => (
                  <Chip
                    key={example}
                    onClick={() => {
                      setQuery(example);
                      updateParams({ q: example });
                    }}
                  >
                    {example}
                  </Chip>
                ))}
              </ChipGroup>
            </section>
          ) : (
            <SearchResults
              state={state}
              query={query}
              spaces={spaces}
              onRetry={retry}
              onResetFilters={spaceIds.length > 0 ? resetFilters : undefined}
            />
          )}
        </div>
      </div>
    </>
  );
}
