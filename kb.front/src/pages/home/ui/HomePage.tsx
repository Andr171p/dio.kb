import { Clock, FileText, FolderOpen, Search } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router';
import {
  ArticleStatusBadge,
  loadSpaceArticles,
  useSpaceArticles,
} from '@entities/article';
import { displayName, useCurrentUser } from '@entities/session';
import { loadSpaces, SpaceIcon, useSpaces } from '@entities/space';
import { SidebarToggle } from '@widgets/app-sidebar';
import { useRecentArticles } from '@widgets/global-search';
import { routes } from '@shared/config/routes';
import { formatRelative } from '@shared/lib/format';
import { EmptyState } from '@shared/ui/empty-state';
import { Skeleton } from '@shared/ui/skeleton';
import { Topbar } from '@shared/ui/topbar';
import styles from './HomePage.module.scss';

const RECENT_LIMIT = 8;

function greeting(date = new Date()): string {
  const hour = date.getHours();
  if (hour < 5) return 'Доброй ночи';
  if (hour < 12) return 'Доброе утро';
  if (hour < 18) return 'Добрый день';
  return 'Добрый вечер';
}

export function HomePage() {
  const user = useCurrentUser();
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

  return (
    <>
      <Topbar start={<SidebarToggle />} />
      <div className={styles.page}>
        <section className={styles.hero}>
          <h1 className={styles.title}>
            {greeting()}
            {user ? `, ${displayName(user).split(' ')[0]}` : ''}
          </h1>
          <p className={styles.subtitle}>
            Инструкции, регламенты и проверенные решения для работы с заявками.
          </p>
          <form
            className={styles.search}
            role="search"
            onSubmit={(event) => {
              event.preventDefault();
              if (query.trim()) void navigate(routes.search(query.trim()));
            }}
          >
            <Search size={18} className={styles.searchIcon} aria-hidden />
            <input
              className={styles.searchInput}
              value={query}
              placeholder="Опишите проблему или вопрос — найдём подходящие статьи"
              aria-label="Поиск по базе знаний"
              onChange={(event) => setQuery(event.target.value)}
            />
          </form>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Пространства</h2>
          {spacesStatus === 'loading' && spaces.length === 0 ? (
            <div className={styles.spaces}>
              {[0, 1, 2].map((index) => (
                <Skeleton key={index} height={112} />
              ))}
            </div>
          ) : spaces.length === 0 ? (
            <EmptyState
              icon={FolderOpen}
              title="Нет доступных пространств"
              description="Попросите администратора DIOS выдать вам доступ к нужному пространству."
            />
          ) : (
            <div className={styles.spaces}>
              {spaces.map((space) => {
                const articles = bySpace[space.id];
                return (
                  <Link
                    key={space.id}
                    to={routes.space(space.id)}
                    className={styles.spaceCard}
                  >
                    <div className={styles.spaceHeader}>
                      <SpaceIcon spaceKey={space.key} size="md" />
                      <div className={styles.spaceTitles}>
                        <span className={styles.spaceName}>{space.name}</span>
                        <span className={styles.spaceKey}>{space.key}</span>
                      </div>
                    </div>
                    <p className={styles.spaceDescription}>
                      {space.description ?? 'Без описания'}
                    </p>
                    <span className={styles.spaceMeta}>
                      {articles?.status === 'ready'
                        ? `${articles.items.length} ${pluralizeArticles(articles.items.length)}`
                        : ' '}
                    </span>
                  </Link>
                );
              })}
            </div>
          )}
        </section>

        <div className={styles.columns}>
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Недавно обновлённые</h2>
            {articlesLoading && recentlyUpdated.length === 0 ? (
              <div className={styles.listSkeleton}>
                {[0, 1, 2, 3].map((index) => (
                  <Skeleton key={index} height={44} />
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
                        size={16}
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
                        <ArticleStatusBadge status={article.status} />
                      )}
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Вы открывали</h2>
            {visited.length === 0 ? (
              <p className={styles.muted}>
                Здесь появятся статьи, которые вы читали.
              </p>
            ) : (
              <ul className={styles.list}>
                {visited.map((article) => (
                  <li key={article.id}>
                    <Link
                      to={routes.article(article.id)}
                      className={styles.listItem}
                    >
                      <Clock
                        size={16}
                        className={styles.listIcon}
                        aria-hidden
                      />
                      <span className={styles.listText}>
                        <span className={styles.listTitle}>
                          {article.title}
                        </span>
                        <span className={styles.listMeta}>
                          {spaceNames.get(article.spaceId)} ·{' '}
                          {formatRelative(article.visitedAt)}
                        </span>
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </div>
    </>
  );
}

function pluralizeArticles(count: number): string {
  const forms: Partial<Record<Intl.LDMLPluralRule, string>> = {
    one: 'статья',
    few: 'статьи',
    many: 'статей',
  };
  return forms[new Intl.PluralRules('ru-RU').select(count)] ?? 'статьи';
}
