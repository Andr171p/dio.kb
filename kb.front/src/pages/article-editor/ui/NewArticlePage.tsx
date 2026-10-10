import { FolderLock } from 'lucide-react';
import { useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router';
import { hasPermission } from '@entities/access-grant';
import { loadSpaces, useSpace, useSpaces } from '@entities/space';
import { revealInSidebar, SidebarToggle } from '@widgets/app-sidebar';
import { ArticleEditor } from '@widgets/article-editor';
import { routes } from '@shared/config/routes';
import { Breadcrumbs } from '@shared/ui/breadcrumbs';
import { ButtonLink } from '@shared/ui/button';
import { EmptyState } from '@shared/ui/empty-state';
import { Spinner } from '@shared/ui/spinner';
import { Topbar } from '@shared/ui/topbar';
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

  if (!space && spacesStatus !== 'ready' && spacesStatus !== 'error')
    return (
      <>
        <Topbar start={<SidebarToggle />} />
        <div className={styles.loading}>
          <Spinner size={20} label="Загрузка" />
        </div>
      </>
    );

  if (!space || !hasPermission(space.permissions, 'WRITE'))
    return (
      <>
        <Topbar start={<SidebarToggle />} />
        <EmptyState
          icon={FolderLock}
          title="Нельзя создать статью"
          description="У вас нет права на редактирование в этом пространстве."
          action={<ButtonLink to={routes.home()}>На главную</ButtonLink>}
        />
      </>
    );

  return (
    <ArticleEditor
      key={`${spaceId}:${collectionId ?? ''}`}
      target={{ kind: 'new', spaceId, collectionId }}
      permissions={space.permissions}
      topbarStart={
        <>
          <SidebarToggle />
          <Breadcrumbs
            items={[
              { label: space.name, to: routes.space(space.id) },
              { label: 'Новая статья' },
            ]}
          />
        </>
      }
      onCreated={(detail) =>
        void navigate(routes.editArticle(detail.article.id), { replace: true })
      }
      onPublished={(detail) => void navigate(routes.article(detail.article.id))}
      onClose={() => void navigate(routes.space(spaceId))}
    />
  );
}
