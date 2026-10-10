import {
  Archive,
  ArchiveRestore,
  Eye,
  FileClock,
  FileQuestion,
  FileText,
  History,
  Link2,
  MoreHorizontal,
  Pencil,
  Printer,
  Send,
  Shield,
  Undo2,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router';
import { hasPermission } from '@entities/access-grant';
import {
  ArticleStatusBadge,
  loadArticle,
  useArticleEntry,
  type ArticleDetail,
} from '@entities/article';
import {
  findNodePath,
  loadNavigation,
  useSpaceNavigation,
} from '@entities/collection';
import { isAdmin, useCurrentUser } from '@entities/session';
import { loadSpaces, useSpace } from '@entities/space';
import {
  archiveArticle,
  publishArticle,
  restoreArticle,
  unpublishArticle,
} from '@features/article-lifecycle';
import {
  openSidebarDialog,
  revealInSidebar,
  SidebarToggle,
} from '@widgets/app-sidebar';
import { ArticleReader } from '@widgets/article-viewer';
import {
  forgetArticleVisit,
  rememberArticleVisit,
} from '@widgets/global-search';
import { routes } from '@shared/config/routes';
import { useCopyToClipboard } from '@shared/lib/hooks';
import { Breadcrumbs, type Crumb } from '@shared/ui/breadcrumbs';
import { Button, ButtonLink, IconButton } from '@shared/ui/button';
import { Callout } from '@shared/ui/callout';
import { confirmAction } from '@shared/ui/dialog';
import { EmptyState } from '@shared/ui/empty-state';
import { Menu, MenuItem, MenuSeparator } from '@shared/ui/menu';
import { usePopover } from '@shared/ui/popover';
import { Skeleton } from '@shared/ui/skeleton';
import { toast } from '@shared/ui/toast';
import { Topbar } from '@shared/ui/topbar';
import styles from './ArticlePage.module.scss';

type View = 'published' | 'draft';

/**
 * Читатель видит опубликованную редакцию. Черновик загружается, только если
 * опубликованной нет или редактор явно переключился на него.
 */
function useArticleForReading(articleId: string, view: View) {
  const published = useArticleEntry(articleId, 'published');
  const draft = useArticleEntry(articleId, 'draft');

  useEffect(() => {
    void loadArticle(articleId, 'published');
  }, [articleId]);

  const publishedMissing = published?.status === 'error';
  const wantsDraft = view === 'draft' || publishedMissing;

  useEffect(() => {
    if (wantsDraft) void loadArticle(articleId, 'draft');
  }, [articleId, wantsDraft]);

  if (!published || published.status === 'loading')
    return { status: 'loading' as const };

  if (!publishedMissing && view === 'published' && published.data)
    return {
      status: 'ready' as const,
      detail: published.data,
      version: 'published' as const,
      published: published.data,
    };

  if (!draft || draft.status === 'loading')
    return { status: 'loading' as const };
  if (draft.data)
    return {
      status: 'ready' as const,
      detail: draft.data,
      version: 'draft' as const,
      published: published.data,
    };

  return { status: 'missing' as const };
}

function ArticleActions({
  detail,
  version,
  onViewChange,
}: {
  detail: ArticleDetail;
  version: View;
  onViewChange: (view: View) => void;
}) {
  const { article, permissions, revision } = detail;
  const user = useCurrentUser();
  const { triggerProps, popoverProps } = usePopover();
  const { copy } = useCopyToClipboard();
  const [publishing, setPublishing] = useState(false);

  const canWrite = hasPermission(permissions, 'WRITE');
  const canPublish = hasPermission(permissions, 'PUBLISH');
  const canArchive = hasPermission(permissions, 'ARCHIVE');
  const archived = article.status === 'archived';
  const needsPublish =
    !archived && (article.status === 'draft' || article.hasUnpublishedChanges);

  const publish = async () => {
    setPublishing(true);
    if (await publishArticle(article)) onViewChange('published');
    setPublishing(false);
  };

  return (
    <>
      {canWrite && !archived && (
        <ButtonLink
          to={routes.articleHistory(article.id)}
          variant="ghost"
          size="sm"
          icon={History}
        >
          <span className={styles.hideMobile}>История</span>
        </ButtonLink>
      )}
      {canWrite && !archived && (
        <ButtonLink
          to={routes.editArticle(article.id)}
          variant={needsPublish && canPublish ? 'secondary' : 'primary'}
          size="sm"
          icon={Pencil}
          aria-label="Редактировать"
        >
          <span className={styles.hideMobile}>Редактировать</span>
        </ButtonLink>
      )}
      {canPublish && needsPublish && (
        <Button
          variant="primary"
          size="sm"
          icon={Send}
          loading={publishing}
          onClick={() => void publish()}
        >
          Опубликовать
        </Button>
      )}

      <IconButton icon={MoreHorizontal} label="Ещё" {...triggerProps} />
      <Menu {...popoverProps} placement="bottom-end">
        <MenuItem
          icon={Link2}
          onSelect={() =>
            void copy(
              `${window.location.origin}${routes.article(article.id)}`,
            ).then(() => toast.success('Ссылка скопирована'))
          }
        >
          Копировать ссылку
        </MenuItem>
        <MenuItem icon={Printer} onSelect={() => window.print()}>
          Печать или PDF
        </MenuItem>
        {canWrite &&
          article.publishedRevisionId &&
          article.hasUnpublishedChanges && (
            <MenuItem
              icon={Eye}
              onSelect={() =>
                onViewChange(version === 'draft' ? 'published' : 'draft')
              }
            >
              {version === 'draft'
                ? 'Опубликованная версия'
                : 'Посмотреть черновик'}
            </MenuItem>
          )}
        {isAdmin(user) && (
          <MenuItem
            icon={Shield}
            onSelect={() =>
              openSidebarDialog({
                kind: 'access',
                resource: { type: 'article', id: article.id },
                title: revision.title,
                spaceId: article.spaceId,
              })
            }
          >
            Доступ
          </MenuItem>
        )}
        {(canPublish || canArchive) && <MenuSeparator />}
        {canPublish && article.status === 'published' && (
          <MenuItem
            icon={Undo2}
            onSelect={() =>
              confirmAction({
                title: 'Снять статью с публикации?',
                description:
                  'Читатели и поиск перестанут её видеть сразу. Текст и история сохранятся — статью можно опубликовать снова.',
                confirmLabel: 'Снять с публикации',
                tone: 'danger',
                onConfirm: () => unpublishArticle(article),
              })
            }
          >
            Снять с публикации
          </MenuItem>
        )}
        {canArchive && !archived && (
          <MenuItem
            icon={Archive}
            tone="danger"
            onSelect={() =>
              confirmAction({
                title: 'Переместить статью в архив?',
                description:
                  'Статья пропадёт у читателей и из поиска. Её можно будет восстановить как черновик.',
                confirmLabel: 'В архив',
                tone: 'danger',
                onConfirm: () => archiveArticle(article),
              })
            }
          >
            В архив
          </MenuItem>
        )}
      </Menu>
    </>
  );
}

function ArticleNotice({
  detail,
  version,
  published,
  onViewChange,
}: {
  detail: ArticleDetail;
  version: View;
  published: ArticleDetail | null;
  onViewChange: (view: View) => void;
}) {
  const { article, permissions } = detail;
  const [restoring, setRestoring] = useState(false);

  if (article.status === 'archived')
    return (
      <Callout
        icon={Archive}
        tone="neutral"
        title="Статья в архиве"
        actions={
          hasPermission(permissions, 'ARCHIVE') && (
            <Button
              size="sm"
              icon={ArchiveRestore}
              loading={restoring}
              onClick={() => {
                setRestoring(true);
                restoreArticle(article)
                  .catch(() => undefined)
                  .finally(() => setRestoring(false));
              }}
            >
              Восстановить
            </Button>
          )
        }
      >
        Читатели и поиск её не видят. Восстановленная статья станет черновиком.
      </Callout>
    );

  if (!article.publishedRevisionId)
    return (
      <Callout icon={FileClock} tone="warning" title="Черновик">
        Статья ещё не опубликована — её видят только редакторы пространства.
      </Callout>
    );

  if (version === 'draft')
    return (
      <Callout
        icon={FileClock}
        tone="warning"
        title={`Черновик · редакция ${detail.revision.number}`}
        actions={
          <Button size="sm" onClick={() => onViewChange('published')}>
            Опубликованная версия
          </Button>
        }
      >
        Читатели видят опубликованную редакцию
        {published ? ` ${published.revision.number}` : ''}, пока изменения не
        опубликованы.
      </Callout>
    );

  if (article.hasUnpublishedChanges && hasPermission(permissions, 'WRITE'))
    return (
      <Callout
        icon={FileText}
        tone="info"
        title="Есть неопубликованные изменения"
        actions={
          <Button size="sm" icon={Eye} onClick={() => onViewChange('draft')}>
            Посмотреть черновик
          </Button>
        }
      >
        Текущая редакция {article.revisionNumber} ещё не видна читателям.
      </Callout>
    );

  return null;
}

export function ArticlePage() {
  const { articleId = '' } = useParams();
  // Выбор версии относится к конкретной статье: при переходе снова показываем опубликованную
  const [viewState, setViewState] = useState<{ articleId: string; view: View }>(
    {
      articleId,
      view: 'published',
    },
  );
  const view = viewState.articleId === articleId ? viewState.view : 'published';
  const setView = (next: View) => setViewState({ articleId, view: next });
  const result = useArticleForReading(articleId, view);
  const detail = result.status === 'ready' ? result.detail : null;
  const spaceId = detail?.article.spaceId;
  const space = useSpace(spaceId);
  const navigation = useSpaceNavigation(spaceId)?.data;

  useEffect(() => {
    void loadSpaces();
    if (spaceId) void loadNavigation(spaceId);
  }, [spaceId]);

  const path = navigation
    ? findNodePath(
        navigation,
        (node) => node.type === 'article' && node.id === articleId,
      )
    : null;

  useEffect(() => {
    if (!spaceId) return;
    revealInSidebar([
      spaceId,
      ...(path?.slice(0, -1).map((node) => node.id) ?? []),
    ]);
    // Путь пересчитывается при каждой загрузке дерева; раскрываем, когда он стал известен
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [spaceId, path?.length]);

  useEffect(() => {
    if (detail)
      rememberArticleVisit({
        id: detail.article.id,
        title: detail.revision.title,
        spaceId: detail.article.spaceId,
      });
  }, [detail]);

  useEffect(() => {
    if (result.status === 'missing') forgetArticleVisit(articleId);
  }, [result.status, articleId]);

  const crumbs: Crumb[] = [
    ...(space ? [{ label: space.name, to: routes.space(space.id) }] : []),
    ...(path?.slice(0, -1).map((node) => ({ label: node.title })) ?? []),
    ...(detail ? [{ label: detail.revision.title }] : []),
  ];

  return (
    <>
      <Topbar
        start={
          <>
            <SidebarToggle />
            <Breadcrumbs items={crumbs} />
          </>
        }
        end={
          detail && (
            <ArticleActions
              detail={detail}
              version={result.status === 'ready' ? result.version : 'published'}
              onViewChange={setView}
            />
          )
        }
        className={styles.topbar}
      />

      {result.status === 'loading' && (
        <div className={styles.skeleton}>
          <Skeleton height={40} width="70%" />
          <Skeleton height={14} width="40%" />
          <div className={styles.skeletonBody}>
            {[100, 95, 98, 60, 0, 90, 97, 80].map((width, index) =>
              width ? (
                <Skeleton key={index} height={14} width={`${width}%`} />
              ) : (
                <br key={index} />
              ),
            )}
          </div>
        </div>
      )}

      {result.status === 'missing' && (
        <EmptyState
          icon={FileQuestion}
          title="Статья не найдена"
          description="Возможно, её сняли с публикации, архивировали или у вас нет доступа."
          action={<ButtonLink to={routes.home()}>На главную</ButtonLink>}
        />
      )}

      {result.status === 'ready' && (
        <ArticleReader
          key={result.detail.revision.id}
          detail={result.detail}
          badges={
            result.detail.article.status !== 'published' && (
              <ArticleStatusBadge status={result.detail.article.status} />
            )
          }
          notice={
            <ArticleNotice
              detail={result.detail}
              version={result.version}
              published={result.published}
              onViewChange={setView}
            />
          }
        />
      )}
    </>
  );
}
