import clsx from 'clsx';
import { FileText, Folder, Plus, Shield } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router';
import { hasPermission } from '@entities/access-grant';
import {
  ArticleStatusBadge,
  loadSpaceArticles,
  useSpaceArticles,
} from '@entities/article';
import {
  flattenCollections,
  loadNavigation,
  useSpaceNavigation,
  type NavigationNode,
} from '@entities/collection';
import { isAdmin, useCurrentUser } from '@entities/session';
import { loadSpaces, useSpace, useSpaces } from '@entities/space';
import {
  AppHeader,
  NavigationNodeMenu,
  openSidebarDialog,
  revealInSidebar,
} from '@widgets/app-shell';
import { routes } from '@shared/config/routes';
import { formatShortDate, pluralize } from '@shared/lib/format';
import { MOD_KEY_LABEL } from '@shared/lib/hooks';
import { Button, ButtonLink } from '@shared/ui/button';
import { EmptyState } from '@shared/ui/empty-state';
import { SearchField } from '@shared/ui/search-field';
import { Skeleton } from '@shared/ui/skeleton';
import styles from './SpacePage.module.scss';

/** Псевдо-коллекция для статей, которые не размещены ни в одной коллекции */
const UNPLACED = 'unplaced';

function countArticles(node: NavigationNode): number {
  return node.children.reduce(
    (total, child) =>
      total + (child.type === 'article' ? 1 : countArticles(child)),
    0,
  );
}

export function SpacePage() {
  const { spaceId = '' } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const user = useCurrentUser();
  const space = useSpace(spaceId);
  const spacesStatus = useSpaces((state) => state.status);
  const navigation = useSpaceNavigation(spaceId);
  const articles = useSpaceArticles((state) => state.bySpace[spaceId]);
  const [query, setQuery] = useState('');

  useEffect(() => {
    void loadSpaces();
    void loadNavigation(spaceId);
    void loadSpaceArticles(spaceId);
    revealInSidebar([spaceId]);
  }, [spaceId]);

  const data = navigation?.data;
  const collections = useMemo(
    () => (data ? flattenCollections(data.collections) : []),
    [data],
  );
  const summaries = useMemo(
    () => new Map(articles?.items.map((item) => [item.id, item]) ?? []),
    [articles],
  );

  if (spacesStatus === 'ready' && !space)
    return (
      <>
        <AppHeader crumbs={[{ label: 'Пространство' }]} />
        <div className={styles.page}>
          <EmptyState
            title="Пространство не найдено"
            description="Возможно, оно архивировано или у вас нет к нему доступа."
            action={<ButtonLink to={routes.home()}>На главную</ButtonLink>}
          />
        </div>
      </>
    );

  const canWrite = hasPermission(space?.permissions, 'WRITE');
  const hasUnplaced = (data?.unplacedArticles.length ?? 0) > 0;
  const requested = searchParams.get('collection');
  const selectedId =
    requested &&
    (requested === UNPLACED
      ? hasUnplaced
      : collections.some(({ node }) => node.id === requested))
      ? requested
      : (collections[0]?.node.id ?? (hasUnplaced ? UNPLACED : null));
  const selected =
    collections.find(({ node }) => node.id === selectedId)?.node ?? null;
  const items =
    selectedId === UNPLACED
      ? (data?.unplacedArticles ?? [])
      : selected?.children;
  const empty = data && collections.length === 0 && !hasUnplaced;

  const select = (id: string) =>
    setSearchParams({ collection: id }, { replace: true });

  return (
    <>
      <AppHeader
        crumbs={[
          { label: 'Пространства', to: routes.home() },
          { label: space?.name ?? '…' },
        ]}
      />

      <div className={styles.page}>
        <header className={styles.header}>
          <div className={styles.headerText}>
            {space ? (
              <>
                <h1 className={styles.title}>{space.name}</h1>
                {space.description && (
                  <p className={styles.description}>{space.description}</p>
                )}
              </>
            ) : (
              <Skeleton height={44} width={320} />
            )}
          </div>
          {space && (
            <div className={styles.headerActions}>
              {isAdmin(user) && (
                <ButtonLink
                  to={routes.access({ type: 'space', id: space.id })}
                  icon={Shield}
                >
                  Доступ
                </ButtonLink>
              )}
              {canWrite && (
                <ButtonLink
                  to={routes.newArticle(
                    space.id,
                    selected ? selected.id : undefined,
                  )}
                  variant="primary"
                  className={styles.newArticle}
                >
                  Новая статья
                </ButtonLink>
              )}
            </div>
          )}
        </header>

        <form
          className={styles.search}
          role="search"
          onSubmit={(event) => {
            event.preventDefault();
            if (query.trim())
              void navigate(
                `${routes.search(query.trim())}&space=${encodeURIComponent(spaceId)}`,
              );
          }}
        >
          <SearchField
            value={query}
            placeholder={`Поиск в пространстве «${space?.name ?? '…'}»`}
            aria-label="Поиск в пространстве"
            shortcut={[MOD_KEY_LABEL, 'K']}
            onChange={(event) => setQuery(event.target.value)}
          />
        </form>

        {navigation?.status === 'loading' && !data && (
          <div className={styles.layout}>
            <div className={styles.skeletonColumn}>
              {[0, 1, 2, 3].map((index) => (
                <Skeleton key={index} height={36} />
              ))}
            </div>
            <div className={styles.skeletonColumn}>
              {[0, 1, 2].map((index) => (
                <Skeleton key={index} height={52} />
              ))}
            </div>
          </div>
        )}

        {empty && (
          <EmptyState
            className={styles.empty}
            title="В пространстве пока нет статей"
            description={
              canWrite
                ? 'Создайте первую статью или коллекцию, чтобы выстроить структуру.'
                : 'Статьи появятся здесь после публикации.'
            }
            action={
              canWrite && (
                <>
                  <ButtonLink to={routes.newArticle(spaceId)} variant="primary">
                    Новая статья
                  </ButtonLink>
                  <Button
                    icon={Plus}
                    onClick={() =>
                      openSidebarDialog({
                        kind: 'create-collection',
                        spaceId,
                        parent: null,
                      })
                    }
                  >
                    Создать коллекцию
                  </Button>
                </>
              )
            }
          />
        )}

        {data && !empty && (
          <div className={styles.layout}>
            <nav className={styles.collections} aria-label="Коллекции">
              <h2 className={styles.columnLabel}>Коллекции</h2>
              <ul className={styles.collectionList}>
                {collections.map(({ node, depth }) => (
                  <li key={node.id}>
                    <button
                      type="button"
                      className={clsx(
                        styles.collection,
                        node.id === selectedId && styles.collectionActive,
                      )}
                      style={{ paddingLeft: 16 + depth * 16 }}
                      aria-current={node.id === selectedId ? 'true' : undefined}
                      onClick={() => select(node.id)}
                    >
                      {node.title}
                    </button>
                  </li>
                ))}
                {hasUnplaced && (
                  <li>
                    <button
                      type="button"
                      className={clsx(
                        styles.collection,
                        styles.unplaced,
                        selectedId === UNPLACED && styles.collectionActive,
                      )}
                      aria-current={
                        selectedId === UNPLACED ? 'true' : undefined
                      }
                      onClick={() => select(UNPLACED)}
                    >
                      Вне коллекций
                    </button>
                  </li>
                )}
              </ul>
              {canWrite && (
                <Button
                  className={styles.createCollection}
                  onClick={() =>
                    openSidebarDialog({
                      kind: 'create-collection',
                      spaceId,
                      parent: null,
                    })
                  }
                >
                  + Создать коллекцию
                </Button>
              )}
            </nav>

            <section className={styles.content} aria-live="polite">
              <header className={styles.contentHeader}>
                <div>
                  <h2 className={styles.contentTitle}>
                    {selectedId === UNPLACED
                      ? 'Вне коллекций'
                      : (selected?.title ?? '')}
                  </h2>
                  <p className={styles.contentMeta}>
                    {selectedId === UNPLACED
                      ? 'Статьи, которые ещё не размещены ни в одной коллекции.'
                      : selected &&
                        pluralize(countArticles(selected), [
                          'статья',
                          'статьи',
                          'статей',
                        ])}
                  </p>
                </div>
                {space && selected && (
                  <NavigationNodeMenu space={space} node={selected} />
                )}
              </header>

              {items && items.length === 0 ? (
                <p className={styles.contentEmpty}>
                  В коллекции пока пусто.
                  {canWrite && selected && (
                    <>
                      {' '}
                      <Link to={routes.newArticle(spaceId, selected.id)}>
                        Добавить статью
                      </Link>
                    </>
                  )}
                </p>
              ) : (
                <ul className={styles.items}>
                  {items?.map((child) => {
                    const summary = summaries.get(child.id);
                    return (
                      <li key={child.placementId ?? child.id}>
                        {child.type === 'article' ? (
                          <Link
                            to={routes.article(child.id)}
                            className={styles.item}
                          >
                            <FileText
                              size={17}
                              strokeWidth={1.5}
                              className={styles.itemIcon}
                              aria-hidden
                            />
                            <span className={styles.itemText}>
                              <span className={styles.itemTitle}>
                                {child.title}
                              </span>
                              {summary && (
                                <span className={styles.itemMeta}>
                                  Обновлено {formatShortDate(summary.updatedAt)}
                                </span>
                              )}
                            </span>
                            {child.status && child.status !== 'published' && (
                              <ArticleStatusBadge
                                status={child.status}
                                size="sm"
                              />
                            )}
                          </Link>
                        ) : (
                          <button
                            type="button"
                            className={styles.item}
                            onClick={() => select(child.id)}
                          >
                            <Folder
                              size={17}
                              strokeWidth={1.5}
                              className={styles.itemIcon}
                              aria-hidden
                            />
                            <span className={styles.itemText}>
                              <span className={styles.itemTitle}>
                                {child.title}
                              </span>
                              <span className={styles.itemMeta}>
                                Коллекция ·{' '}
                                {pluralize(countArticles(child), [
                                  'статья',
                                  'статьи',
                                  'статей',
                                ])}
                              </span>
                            </span>
                          </button>
                        )}
                      </li>
                    );
                  })}
                </ul>
              )}

              <p className={styles.footnote}>
                Статьи могут входить в несколько коллекций.
              </p>
            </section>
          </div>
        )}
      </div>
    </>
  );
}
