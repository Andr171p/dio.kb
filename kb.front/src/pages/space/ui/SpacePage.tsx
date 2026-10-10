import {
  FilePlus,
  FileText,
  Folder,
  FolderPlus,
  Search,
  Shield,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router';
import { hasPermission } from '@entities/access-grant';
import {
  loadNavigation,
  useSpaceNavigation,
  type NavigationNode,
} from '@entities/collection';
import { isAdmin, useCurrentUser } from '@entities/session';
import { loadSpaces, SpaceIcon, useSpace, useSpaces } from '@entities/space';
import {
  openSidebarDialog,
  revealInSidebar,
  SidebarToggle,
} from '@widgets/app-sidebar';
import { routes } from '@shared/config/routes';
import { Breadcrumbs } from '@shared/ui/breadcrumbs';
import { Button, ButtonLink, IconButton } from '@shared/ui/button';
import { EmptyState } from '@shared/ui/empty-state';
import { Skeleton } from '@shared/ui/skeleton';
import { Topbar } from '@shared/ui/topbar';
import styles from './SpacePage.module.scss';

const PREVIEW_LIMIT = 6;

function countArticles(node: NavigationNode): number {
  return node.children.reduce(
    (total, child) =>
      total + (child.type === 'article' ? 1 : countArticles(child)),
    0,
  );
}

function CollectionCard({ node }: { node: NavigationNode }) {
  const children = node.children.slice(0, PREVIEW_LIMIT);
  const rest = node.children.length - children.length;
  const total = countArticles(node);

  return (
    <article className={styles.collection}>
      <header className={styles.collectionHeader}>
        <Folder size={16} className={styles.collectionIcon} aria-hidden />
        <h3 className={styles.collectionTitle}>{node.title}</h3>
        <span className={styles.collectionCount}>{total}</span>
      </header>
      {children.length === 0 ? (
        <p className={styles.collectionEmpty}>Пусто</p>
      ) : (
        <ul className={styles.collectionList}>
          {children.map((child) => (
            <li key={child.placementId ?? child.id}>
              {child.type === 'article' ? (
                <Link
                  to={routes.article(child.id)}
                  className={styles.collectionItem}
                >
                  <FileText size={14} aria-hidden />
                  <span className={styles.itemTitle}>{child.title}</span>
                  {child.status === 'draft' && (
                    <span className={styles.draft}>черновик</span>
                  )}
                </Link>
              ) : (
                <button
                  type="button"
                  className={styles.collectionItem}
                  onClick={() => revealInSidebar([child.id])}
                >
                  <Folder size={14} aria-hidden />
                  <span className={styles.itemTitle}>{child.title}</span>
                  <span className={styles.draft}>{countArticles(child)}</span>
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
      {rest > 0 && (
        <button
          type="button"
          className={styles.more}
          onClick={() => revealInSidebar([node.id])}
        >
          Ещё {rest} — показать в навигации
        </button>
      )}
    </article>
  );
}

export function SpacePage() {
  const { spaceId = '' } = useParams();
  const navigate = useNavigate();
  const user = useCurrentUser();
  const space = useSpace(spaceId);
  const spacesStatus = useSpaces((state) => state.status);
  const navigation = useSpaceNavigation(spaceId);
  const [query, setQuery] = useState('');

  useEffect(() => {
    void loadSpaces();
    void loadNavigation(spaceId);
    revealInSidebar([spaceId]);
  }, [spaceId]);

  if (spacesStatus === 'ready' && !space)
    return (
      <>
        <Topbar start={<SidebarToggle />} />
        <EmptyState
          icon={Folder}
          title="Пространство не найдено"
          description="Возможно, оно архивировано или у вас нет к нему доступа."
          action={<ButtonLink to={routes.home()}>На главную</ButtonLink>}
        />
      </>
    );

  const canWrite = hasPermission(space?.permissions, 'WRITE');
  const data = navigation?.data;
  const empty =
    data && data.collections.length === 0 && data.unplacedArticles.length === 0;

  return (
    <>
      <Topbar
        start={
          <>
            <SidebarToggle />
            <Breadcrumbs items={[{ label: space?.name ?? '…' }]} />
          </>
        }
        end={
          space && (
            <>
              {isAdmin(user) && (
                <IconButton
                  icon={Shield}
                  label="Доступ к пространству"
                  onClick={() =>
                    openSidebarDialog({
                      kind: 'access',
                      resource: { type: 'space', id: space.id },
                      title: space.name,
                    })
                  }
                />
              )}
              {canWrite && (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={FolderPlus}
                    onClick={() =>
                      openSidebarDialog({
                        kind: 'create-collection',
                        spaceId: space.id,
                        parent: null,
                      })
                    }
                  >
                    Коллекция
                  </Button>
                  <ButtonLink
                    to={routes.newArticle(space.id)}
                    variant="primary"
                    size="sm"
                    icon={FilePlus}
                  >
                    Новая статья
                  </ButtonLink>
                </>
              )}
            </>
          )
        }
      />

      <div className={styles.page}>
        <header className={styles.header}>
          {space ? (
            <>
              <SpaceIcon spaceKey={space.key} size="lg" />
              <div className={styles.headerText}>
                <h1 className={styles.title}>{space.name}</h1>
                <p className={styles.description}>
                  <span className={styles.key}>{space.key}</span>
                  {space.description && <span> · {space.description}</span>}
                </p>
              </div>
            </>
          ) : (
            <Skeleton height={48} width={320} />
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
          <Search size={16} className={styles.searchIcon} aria-hidden />
          <input
            className={styles.searchInput}
            value={query}
            placeholder={`Поиск в «${space?.name ?? 'пространстве'}»`}
            aria-label="Поиск в пространстве"
            onChange={(event) => setQuery(event.target.value)}
          />
        </form>

        {navigation?.status === 'loading' && !data && (
          <div className={styles.grid}>
            {[0, 1, 2].map((index) => (
              <Skeleton key={index} height={180} />
            ))}
          </div>
        )}

        {empty && (
          <EmptyState
            icon={FileText}
            title="В пространстве пока нет статей"
            description={
              canWrite
                ? 'Создайте первую статью или коллекцию, чтобы выстроить структуру.'
                : 'Статьи появятся здесь после публикации.'
            }
            action={
              canWrite && (
                <ButtonLink
                  to={routes.newArticle(spaceId)}
                  variant="primary"
                  icon={FilePlus}
                >
                  Новая статья
                </ButtonLink>
              )
            }
          />
        )}

        {data && data.collections.length > 0 && (
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Коллекции</h2>
            <div className={styles.grid}>
              {data.collections.map((node) => (
                <CollectionCard key={node.id} node={node} />
              ))}
            </div>
          </section>
        )}

        {data && data.unplacedArticles.length > 0 && (
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Статьи вне коллекций</h2>
            <ul className={styles.list}>
              {data.unplacedArticles.map((node) => (
                <li key={node.id}>
                  <Link
                    to={routes.article(node.id)}
                    className={styles.listItem}
                  >
                    <FileText size={16} aria-hidden />
                    <span className={styles.itemTitle}>{node.title}</span>
                    {node.status === 'draft' && (
                      <span className={styles.draft}>черновик</span>
                    )}
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </>
  );
}
