import { ArrowRight, ChevronRight, FileText, FolderOpen } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router';
import {
  ArticleStatusBadge,
  loadSpaceArticles,
  useRecentArticles,
  useSpaceArticles,
} from '@entities/article';
import { loadSpaces, useSpaces } from '@entities/space';
import { AppHeader } from '@widgets/app-shell';
import { routes } from '@shared/config/routes';
import { formatRelative, pluralize } from '@shared/lib/format';
import { MOD_KEY_LABEL } from '@shared/lib/hooks';
import { EmptyState } from '@shared/ui/empty-state';
import { SearchField } from '@shared/ui/search-field';
import { Skeleton } from '@shared/ui/skeleton';
import styles from './HomePage.module.scss';

const RECENT_LIMIT = 6;

export function HomePage() {
  const navigate = useNavigate();
  const { items: spaces, status: spacesStatus } = useSpaces();
  const bySpace = useSpaceArticles((state) => state.bySpace);
  const visited = useRecentArticles((state) => state.items);
  const [query, setQuery] = useState('');

  useEffect(() => {
    void loadSpaces();
  }, []);

  useEffect(() => {
    spaces.forEach((space) => void loadSpaceArticles(space.id));
  }, [spaces]);

  const spaceNames = useMemo(
    () => new Map(spaces.map((space) => [space.id, space.name])),
    [spaces],
  );

  const recentlyUpdated = useMemo(
    () =>
      spaces
        .flatMap((space) => bySpace[space.id]?.items ?? [])
        .filter((article) => article.status !== 'archived')
        .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
        .slice(0, RECENT_LIMIT),
    [spaces, bySpace],
  );

  const articlesLoading =
    spacesStatus !== 'ready' ||
    spaces.some(
      (space) => bySpace[space.id]?.status === 'loading' || !bySpace[space.id],
    );

  const lastVisited = visited.find((article) =>
    spaceNames.has(article.spaceId),
  );

  return (
    <>
      <AppHeader crumbs={[{ label: 'База знаний' }]} />
      <div className={styles.page}>
        <section className={styles.hero}>
          <h1 className={styles.title}>Знания, которые помогают в работе.</h1>
          <p className={styles.subtitle}>
            Инструкции, регламенты и решения команды ДИО — в одном месте.
          </p>
          <form
            className={styles.search}
            role="search"
            onSubmit={(event) => {
              event.preventDefault();
              if (query.trim()) void navigate(routes.search(query.trim()));
            }}
          >
            <SearchField
              value={query}
              placeholder="Найти инструкцию, решение или ответ"
              aria-label="Поиск по базе знаний"
              shortcut={[MOD_KEY_LABEL, 'K']}
              onChange={(event) => setQuery(event.target.value)}
            />
          </form>
        </section>

        {lastVisited && (
          <section className={styles.section}>
            <header className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>Продолжить работу</h2>
              <Link to={routes.recent()} className={styles.sectionLink}>
                Все недавние <ArrowRight size={14} aria-hidden />
              </Link>
            </header>
            <Link
              to={routes.article(lastVisited.id)}
              className={styles.continue}
            >
              <FileText
                size={24}
                strokeWidth={1.5}
                className={styles.continueIcon}
                aria-hidden
              />
              <span className={styles.continueText}>
                <span className={styles.continueTitle}>
                  {lastVisited.title}
                </span>
                <span className={styles.continueMeta}>
                  {spaceNames.get(lastVisited.spaceId)} · Вы открывали{' '}
                  {formatRelative(lastVisited.visitedAt)}
                </span>
              </span>
              <ArrowRight
                size={22}
                strokeWidth={1.6}
                className={styles.continueArrow}
                aria-hidden
              />
            </Link>
          </section>
        )}

        <div className={styles.columns}>
          <section className={styles.updated}>
            <h2 className={styles.sectionTitle}>Недавно обновлено</h2>
            {articlesLoading && recentlyUpdated.length === 0 ? (
              <div className={styles.listSkeleton}>
                {[0, 1, 2].map((index) => (
                  <Skeleton key={index} height={52} />
                ))}
              </div>
            ) : recentlyUpdated.length === 0 ? (
              <p className={styles.muted}>Статей пока нет.</p>
            ) : (
              <ul className={styles.list}>
                {recentlyUpdated.map((article) => (
                  <li key={article.id}>
                    <Link
                      to={routes.article(article.id)}
                      className={styles.listItem}
                    >
                      <FileText
                        size={19}
                        strokeWidth={1.5}
                        className={styles.listIcon}
                        aria-hidden
                      />
                      <span className={styles.listText}>
                        <span className={styles.listTitle}>
                          {article.title}
                        </span>
                        <span className={styles.listMeta}>
                          {spaceNames.get(article.spaceId)} ·{' '}
                          {formatRelative(article.updatedAt)}
                        </span>
                      </span>
                      {article.status !== 'published' && (
                        <ArticleStatusBadge status={article.status} size="sm" />
                      )}
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className={styles.spacesColumn}>
            <h2 className={styles.sectionTitle}>Пространства</h2>
            {spacesStatus === 'loading' && spaces.length === 0 ? (
              <div className={styles.listSkeleton}>
                {[0, 1, 2].map((index) => (
                  <Skeleton key={index} height={44} />
                ))}
              </div>
            ) : spaces.length === 0 ? (
              <EmptyState
                icon={FolderOpen}
                title="Нет доступных пространств"
                description="Попросите администратора DIOS выдать вам доступ к нужному пространству."
              />
            ) : (
              <ul className={styles.spaces}>
                {spaces.map((space) => {
                  const articles = bySpace[space.id];
                  const count =
                    articles?.status === 'ready'
                      ? articles.items.filter(
                          (article) => article.status !== 'archived',
                        ).length
                      : null;
                  return (
                    <li key={space.id}>
                      <Link
                        to={routes.space(space.id)}
                        className={styles.space}
                      >
                        <span className={styles.spaceText}>
                          <span className={styles.spaceName}>{space.name}</span>
                          <span className={styles.spaceMeta}>
                            {count === null
                              ? ' '
                              : pluralize(count, [
                                  'статья',
                                  'статьи',
                                  'статей',
                                ])}
                          </span>
                        </span>
                        <ChevronRight
                          size={16}
                          className={styles.spaceChevron}
                          aria-hidden
                        />
                      </Link>
                    </li>
                  );
                })}
              </ul>
            )}
          </section>
        </div>
      </div>
    </>
  );
}
