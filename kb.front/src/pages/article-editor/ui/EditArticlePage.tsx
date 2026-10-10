import { FileQuestion } from 'lucide-react';
import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router';
import { loadArticle, useArticleEntry } from '@entities/article';
import { loadSpaces, useSpace } from '@entities/space';
import { revealInSidebar, SidebarToggle } from '@widgets/app-sidebar';
import { ArticleEditor } from '@widgets/article-editor';
import { routes } from '@shared/config/routes';
import { Breadcrumbs } from '@shared/ui/breadcrumbs';
import { ButtonLink } from '@shared/ui/button';
import { EmptyState } from '@shared/ui/empty-state';
import { Spinner } from '@shared/ui/spinner';
import { Topbar } from '@shared/ui/topbar';
import styles from './ArticleEditorPage.module.scss';

export function EditArticlePage() {
  const { articleId = '' } = useParams();
  const navigate = useNavigate();
  const entry = useArticleEntry(articleId, 'draft');
  const detail = entry?.data;
  const space = useSpace(detail?.article.spaceId);

  useEffect(() => {
    // Редактор всегда открывает актуальную текущую редакцию
    void loadArticle(articleId, 'draft');
    void loadSpaces();
  }, [articleId]);

  useEffect(() => {
    if (detail) revealInSidebar([detail.article.spaceId]);
  }, [detail]);

  if (!entry || (entry.status === 'loading' && !detail))
    return (
      <>
        <Topbar start={<SidebarToggle />} />
        <div className={styles.loading}>
          <Spinner size={20} label="Загрузка статьи" />
        </div>
      </>
    );

  if (!detail || detail.article.status === 'archived')
    return (
      <>
        <Topbar start={<SidebarToggle />} />
        <EmptyState
          icon={FileQuestion}
          title={
            detail ? 'Статья в архиве' : 'Статья недоступна для редактирования'
          }
          description={
            detail
              ? 'Восстановите статью из архива, чтобы продолжить редактирование.'
              : 'Возможно, у вас нет права на редактирование или статья удалена.'
          }
          action={
            <ButtonLink to={routes.article(articleId)}>К статье</ButtonLink>
          }
        />
      </>
    );

  return (
    <ArticleEditor
      // Новый экземпляр редактора для каждой статьи
      key={detail.article.id}
      target={{ kind: 'edit', detail }}
      permissions={detail.permissions}
      topbarStart={
        <>
          <SidebarToggle />
          <Breadcrumbs
            items={[
              ...(space
                ? [{ label: space.name, to: routes.space(space.id) }]
                : []),
              { label: 'Редактирование статьи' },
            ]}
          />
        </>
      }
      onCreated={() => undefined}
      onPublished={() => void navigate(routes.article(articleId))}
      onClose={() => void navigate(routes.article(articleId))}
    />
  );
}
