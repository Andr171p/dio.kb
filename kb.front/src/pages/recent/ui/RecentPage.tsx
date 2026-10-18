import { FileText } from 'lucide-react';
import { useEffect, useMemo } from 'react';
import { Link } from 'react-router';
import { clearRecentArticles, useRecentArticles } from '@entities/article';
import { loadSpaces, useSpaces } from '@entities/space';
import { AppHeader } from '@widgets/app-shell';
import { routes } from '@shared/config/routes';
import { formatDateTime, formatRelative } from '@shared/lib/format';
import { Button, ButtonLink } from '@shared/ui/button';
import { EmptyState } from '@shared/ui/empty-state';
import styles from './RecentPage.module.scss';

/** Статьи, которые пользователь открывал в этом браузере. */
export function RecentPage() {
  const visited = useRecentArticles((state) => state.items);
  const spaces = useSpaces((state) => state.items);

  useEffect(() => {
    void loadSpaces();
  }, []);

  const spaceNames = useMemo(
    () => new Map(spaces.map((space) => [space.id, space.name])),
    [spaces],
  );

  return (
    <>
      <AppHeader crumbs={[{ label: 'Недавние' }]} />
      <div className={styles.page}>
        <header className={styles.header}>
          <div>
            <h1 className={styles.title}>Недавние</h1>
            <p className={styles.subtitle}>
              Статьи, которые вы открывали в этом браузере.
            </p>
          </div>
          {visited.length > 0 && (
            <Button onClick={clearRecentArticles}>Очистить список</Button>
          )}
        </header>

        {visited.length === 0 ? (
          <EmptyState
            className={styles.empty}
            title="Здесь появятся статьи, которые вы читали"
            description="Найдите нужную инструкцию через поиск или откройте пространство."
            action={
              <ButtonLink to={routes.search()}>Перейти к поиску</ButtonLink>
            }
          />
        ) : (
          <ul className={styles.list}>
            {visited.map((article) => (
              <li key={article.id}>
                <Link to={routes.article(article.id)} className={styles.item}>
                  <FileText
                    size={19}
                    strokeWidth={1.5}
                    className={styles.icon}
                    aria-hidden
                  />
                  <span className={styles.text}>
                    <span className={styles.itemTitle}>{article.title}</span>
                    <span
                      className={styles.meta}
                      title={formatDateTime(article.visitedAt)}
                    >
                      {spaceNames.get(article.spaceId) ?? 'Пространство'} · Вы
                      открывали {formatRelative(article.visitedAt)}
                    </span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}
