import {
  Archive,
  ArchiveRestore,
  Eye,
  History,
  Link2,
  Lock,
  Maximize2,
  MoreHorizontal,
  Pencil,
  Plus,
  Printer,
  Send,
  Type,
  Undo2,
} from 'lucide-react';
import { useEffect, useId, useState } from 'react';
import { useNavigate, useParams } from 'react-router';
import { hasPermission } from '@entities/access-grant';
import {
  ArticleStatusBadge,
  forgetArticleVisit,
  rememberArticleVisit,
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
import { ReadingSettingsPopover } from '@features/reading-settings';
import { AppHeader, revealInSidebar } from '@widgets/app-shell';
import { ArticleReader } from '@widgets/article-viewer';
import { routes } from '@shared/config/routes';
import { useCopyToClipboard, useMediaQuery } from '@shared/lib/hooks';
import type { Crumb } from '@shared/ui/breadcrumbs';
import { Button, ButtonLink, IconButton } from '@shared/ui/button';
import { Callout } from '@shared/ui/callout';
import { confirmAction } from '@shared/ui/dialog';
import { EmptyState } from '@shared/ui/empty-state';
import { Menu, MenuItem, MenuSeparator } from '@shared/ui/menu';
import { usePopover } from '@shared/ui/popover';
import { Skeleton } from '@shared/ui/skeleton';
import { toast } from '@shared/ui/toast';
import {
  useArticleForReading,
  type View,
} from '../model/use-article-for-reading';
import styles from './ArticlePage.module.scss';

function ArticleActions({
  detail,
  version,
  onViewChange,
}: {
  detail: ArticleDetail;
  version: View;
  onViewChange: (view: View) => void;
}) {
  const { article, permissions } = detail;
  const user = useCurrentUser();
  const space = useSpace(article.spaceId);
  const mobile = useMediaQuery('(max-width: 900px)');
  const { triggerProps, popoverProps } = usePopover();
  const settingsId = useId();
  const { copy } = useCopyToClipboard();
  const navigate = useNavigate();
  const [publishing, setPublishing] = useState(false);

  const canWrite = hasPermission(permissions, 'WRITE');
  const canPublish = hasPermission(permissions, 'PUBLISH');
  const canArchive = hasPermission(permissions, 'ARCHIVE');
  const canCreate = hasPermission(space?.permissions, 'WRITE');
  const archived = article.status === 'archived';
  const needsPublish =
    canPublish &&
    !archived &&
    (article.status === 'draft' || article.hasUnpublishedChanges);
  const canEdit = canWrite && !archived;

  const publish = async () => {
    setPublishing(true);
    if (await publishArticle(article)) onViewChange('published');
    setPublishing(false);
  };

  // Панель настроек открывается после закрытия меню, иначе меню закроет её
  const openReadingSettings = () =>
    requestAnimationFrame(() =>
      document.getElementById(settingsId)?.showPopover(),
    );

  return (
    <>
      {!mobile && needsPublish && (
        <Button
          variant="primary"
          loading={publishing}
          onClick={() => void publish()}
        >
          Опубликовать
        </Button>
      )}
      {!mobile && canEdit && (
        <ButtonLink to={routes.editArticle(article.id)} icon={Pencil}>
          Изменить
        </ButtonLink>
      )}
      {!mobile && canCreate && (
        <ButtonLink to={routes.newArticle(article.spaceId)} icon={Plus}>
          Новая статья
        </ButtonLink>
      )}
      <IconButton
        icon={MoreHorizontal}
        label="Действия со статьёй"
        variant="secondary"
        size="md"
        tooltip={false}
        {...triggerProps}
      />
      <Menu {...popoverProps} placement="bottom-end" className={styles.menu}>
        {mobile && needsPublish && (
          <MenuItem icon={Send} onSelect={() => void publish()}>
            Опубликовать
          </MenuItem>
        )}
        {mobile && canEdit && (
          <MenuItem
            icon={Pencil}
            onSelect={() => void navigate(routes.editArticle(article.id))}
          >
            Изменить
          </MenuItem>
        )}
        <MenuItem icon={Type} onSelect={openReadingSettings}>
          Настройки чтения
        </MenuItem>
        <MenuItem
          icon={Maximize2}
          onSelect={() => void navigate(routes.articleFocus(article.id))}
        >
          Режим фокуса
        </MenuItem>
        <MenuSeparator />
        {canEdit && (
          <MenuItem
            icon={History}
            onSelect={() => void navigate(routes.articleHistory(article.id))}
          >
            История
          </MenuItem>
        )}
        {isAdmin(user) && (
          <MenuItem
            icon={Lock}
            onSelect={() =>
              void navigate(routes.access({ type: 'article', id: article.id }))
            }
          >
            Доступ
          </MenuItem>
        )}
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
        {mobile && canCreate && (
          <MenuItem
            icon={Plus}
            onSelect={() => void navigate(routes.newArticle(article.spaceId))}
          >
            Новая статья
          </MenuItem>
        )}
        {((canPublish && article.status === 'published') ||
          (canArchive && !archived)) && <MenuSeparator />}
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
            Архивировать
          </MenuItem>
        )}
      </Menu>
      <ReadingSettingsPopover
        id={settingsId}
        anchorRef={popoverProps.anchorRef}
        onFocusMode={() => void navigate(routes.articleFocus(article.id))}
      />
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
        tone="neutral"
        title="Статья в архиве"
        actions={
          hasPermission(permissions, 'ARCHIVE') && (
            <Button
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
      <Callout tone="warning" title="Черновик">
        Статья ещё не опубликована — её видят только редакторы пространства.
      </Callout>
    );

  if (version === 'draft')
    return (
      <Callout
        tone="warning"
        title={`Черновик · редакция ${detail.revision.number}`}
        actions={
          <Button onClick={() => onViewChange('published')}>
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
        tone="warning"
        title="Есть неопубликованные изменения"
        actions={
          <Button onClick={() => onViewChange('draft')}>
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

  const collectionPath = path?.slice(0, -1).map((node) => node.title) ?? [];
  const crumbs: Crumb[] = [
    ...(space ? [{ label: space.name, to: routes.space(space.id) }] : []),
    ...collectionPath.map((label) => ({ label })),
    ...(detail ? [{ label: detail.revision.title }] : []),
  ];

  return (
    <>
      <AppHeader
        crumbs={crumbs}
        actions={
          result.status === 'ready' && (
            <ArticleActions
              detail={result.detail}
              version={result.version}
              onViewChange={setView}
            />
          )
        }
      />

      {result.status === 'loading' && (
        <div className={styles.skeleton}>
          <Skeleton height={12} width="30%" />
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
        <div className={styles.missing}>
          <EmptyState
            title="Статья недоступна"
            description="Возможно, её сняли с публикации или у вас нет доступа."
            action={<ButtonLink to={routes.home()}>На главную</ButtonLink>}
          />
        </div>
      )}

      {result.status === 'ready' && (
        <ArticleReader
          key={result.detail.revision.id}
          detail={result.detail}
          eyebrow={[space?.name, ...collectionPath]
            .filter(Boolean)
            .join('  /  ')}
          status={
            <ArticleStatusBadge
              status={
                result.version === 'draft'
                  ? 'draft'
                  : result.detail.article.status
              }
            />
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
