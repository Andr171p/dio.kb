import { useEffect, type ReactNode } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router';
import { hasPermission } from '@entities/access-grant';
import { loadSpaces, useSpace, useSpaces } from '@entities/space';
import { AppHeader, revealInSidebar } from '@widgets/app-shell';
import { ArticleEditor } from '@widgets/article-editor';
import { ArticleContent } from '@widgets/article-viewer';
import { routes } from '@shared/config/routes';
import { ButtonLink } from '@shared/ui/button';
import { EmptyState } from '@shared/ui/empty-state';
import { Skeleton } from '@shared/ui/skeleton';
import styles from './ArticleEditorPage.module.scss';

export function NewArticlePage() {
  const { spaceId = '' } = useParams();
  const [searchParams] = useSearchParams();
  const collectionId = searchParams.get('collection');
  const navigate = useNavigate();
  const space = useSpace(spaceId);
  const spacesStatus = useSpaces((state) => state.status);

  useEffect(() => {
    void loadSpaces();
    revealInSidebar([spaceId]);
  }, [spaceId]);

  const renderHeader = (actions?: ReactNode) => (
    <AppHeader
      crumbs={[
        ...(space ? [{ label: space.name, to: routes.space(space.id) }] : []),
        { label: 'Новая статья' },
      ]}
      actions={actions}
    />
  );
  const header = renderHeader();

  if (!space && spacesStatus !== 'ready' && spacesStatus !== 'error')
    return (
      <>
        {header}
        <div className={styles.loading}>
          <Skeleton height={20} width="20%" />
          <Skeleton height={40} width="60%" />
        </div>
      </>
    );

  if (!space || !hasPermission(space.permissions, 'WRITE'))
    return (
      <>
        {header}
        <div className={styles.loading}>
          <EmptyState
            title="Нельзя создать статью"
            description="У вас нет права на редактирование в этом пространстве."
            action={<ButtonLink to={routes.home()}>На главную</ButtonLink>}
          />
        </div>
      </>
    );

  return (
    <ArticleEditor
      key={`${spaceId}:${collectionId ?? ''}`}
      target={{ kind: 'new', spaceId, collectionId }}
      permissions={space.permissions}
      renderPreview={(markdown) => <ArticleContent markdown={markdown} />}
      renderHeader={renderHeader}
      onCreated={(detail) =>
        void navigate(routes.editArticle(detail.article.id), {
          replace: true,
        })
      }
      onPublished={(detail) => void navigate(routes.article(detail.article.id))}
    />
  );
}
