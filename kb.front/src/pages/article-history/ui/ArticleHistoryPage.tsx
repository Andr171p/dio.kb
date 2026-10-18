import { useEffect } from 'react';
import { useParams } from 'react-router';
import { loadArticle, useArticleEntry } from '@entities/article';
import { loadSpaces, useSpace } from '@entities/space';
import { AppHeader } from '@widgets/app-shell';
import { ArticleHistory } from '@widgets/article-history';
import { ArticleContent } from '@widgets/article-viewer';
import { routes } from '@shared/config/routes';
import { ButtonLink } from '@shared/ui/button';
import { EmptyState } from '@shared/ui/empty-state';
import { Skeleton } from '@shared/ui/skeleton';
import styles from './ArticleHistoryPage.module.scss';

export function ArticleHistoryPage() {
  const { articleId = '' } = useParams();
  const entry = useArticleEntry(articleId, 'draft');
  const detail = entry?.data;
  const space = useSpace(detail?.article.spaceId);

  useEffect(() => {
    void loadArticle(articleId, 'draft');
    void loadSpaces();
  }, [articleId]);

  const backLink = (
    <ButtonLink to={routes.article(articleId)} className={styles.back}>
      Вернуться к статье
    </ButtonLink>
  );

  return (
    <>
      <AppHeader
        crumbs={[
          ...(space ? [{ label: space.name, to: routes.space(space.id) }] : []),
          ...(detail
            ? [{ label: detail.revision.title, to: routes.article(articleId) }]
            : []),
          { label: 'История' },
        ]}
      />
      <div className={styles.page}>
        <header className={styles.header}>
          <h1 className={styles.title}>История изменений</h1>
          <p className={styles.subtitle}>
            Каждое сохранение создаёт новую редакцию статьи.
          </p>
        </header>

        {!entry || (entry.status === 'loading' && !detail) ? (
          <div className={styles.loading}>
            <Skeleton height={64} width={270} />
            <Skeleton height={64} width={270} />
          </div>
        ) : detail ? (
          <ArticleHistory
            detail={detail}
            onRestored={() => undefined}
            renderContent={(markdown) => <ArticleContent markdown={markdown} />}
            aside={backLink}
          />
        ) : (
          <EmptyState
            title="История недоступна"
            description="Историю редакций видят только редакторы статьи."
            action={backLink}
          />
        )}
      </div>
    </>
  );
}
