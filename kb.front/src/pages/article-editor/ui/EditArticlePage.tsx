import { useEffect, type ReactNode } from 'react';
import { useNavigate, useParams } from 'react-router';
import { loadArticle, useArticleEntry } from '@entities/article';
import { loadSpaces, useSpace } from '@entities/space';
import { AppHeader, revealInSidebar } from '@widgets/app-shell';
import { ArticleEditor } from '@widgets/article-editor';
import { ArticleContent } from '@widgets/article-viewer';
import { routes } from '@shared/config/routes';
import { ButtonLink } from '@shared/ui/button';
import { EmptyState } from '@shared/ui/empty-state';
import { Skeleton } from '@shared/ui/skeleton';
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

  const renderHeader = (actions?: ReactNode) => (
    <AppHeader
      crumbs={[
        ...(space ? [{ label: space.name, to: routes.space(space.id) }] : []),
        ...(detail
          ? [{ label: detail.revision.title, to: routes.article(articleId) }]
          : []),
        { label: 'Редактирование' },
      ]}
      actions={actions}
    />
  );
  const header = renderHeader();

  if (!entry || (entry.status === 'loading' && !detail))
    return (
      <>
        {header}
        <div className={styles.loading}>
          <Skeleton height={20} width="20%" />
          <Skeleton height={40} width="60%" />
          <Skeleton height={14} width="80%" />
        </div>
      </>
    );

  if (!detail || detail.article.status === 'archived')
    return (
      <>
        {header}
        <div className={styles.loading}>
          <EmptyState
            title={
              detail
                ? 'Статья в архиве'
                : 'Статья недоступна для редактирования'
            }
            description={
              detail
                ? 'Восстановите статью из архива, чтобы продолжить редактирование.'
                : 'Возможно, у вас нет права на редактирование или статья удалена.'
            }
            action={
              <ButtonLink to={routes.article(articleId)}>
                Вернуться к статье
              </ButtonLink>
            }
          />
        </div>
      </>
    );

  return (
    <ArticleEditor
      // Новый экземпляр редактора для каждой статьи
      key={detail.article.id}
      target={{ kind: 'edit', detail }}
      permissions={detail.permissions}
      renderPreview={(markdown) => <ArticleContent markdown={markdown} />}
      renderHeader={renderHeader}
      onCreated={() => undefined}
      onPublished={() => void navigate(routes.article(articleId))}
    />
  );
}
