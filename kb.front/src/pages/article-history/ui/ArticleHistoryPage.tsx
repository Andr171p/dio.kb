import { FileQuestion, FileText } from 'lucide-react';
import { useEffect } from 'react';
import { useParams } from 'react-router';
import { loadArticle, useArticleEntry } from '@entities/article';
import { loadSpaces, useSpace } from '@entities/space';
import { SidebarToggle } from '@widgets/app-sidebar';
import { ArticleHistory } from '@widgets/article-history';
import { ArticleContent } from '@widgets/article-viewer';
import { routes } from '@shared/config/routes';
import { Breadcrumbs } from '@shared/ui/breadcrumbs';
import { ButtonLink } from '@shared/ui/button';
import { EmptyState } from '@shared/ui/empty-state';
import { Spinner } from '@shared/ui/spinner';
import { Topbar } from '@shared/ui/topbar';
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

  return (
    <>
      <Topbar
        start={
          <>
            <SidebarToggle />
            <Breadcrumbs
              items={[
                ...(space
                  ? [{ label: space.name, to: routes.space(space.id) }]
                  : []),
                ...(detail
                  ? [
                      {
                        label: detail.revision.title,
                        to: routes.article(articleId),
                      },
                    ]
                  : []),
                { label: 'История' },
              ]}
            />
          </>
        }
        end={
          <ButtonLink
            to={routes.article(articleId)}
            size="sm"
            variant="ghost"
            icon={FileText}
          >
            К статье
          </ButtonLink>
        }
      />
      {!entry || (entry.status === 'loading' && !detail) ? (
        <div className={styles.loading}>
          <Spinner size={20} label="Загрузка истории" />
        </div>
      ) : detail ? (
        <ArticleHistory
          detail={detail}
          onRestored={() => undefined}
          renderContent={(markdown) => <ArticleContent markdown={markdown} />}
        />
      ) : (
        <EmptyState
          icon={FileQuestion}
          title="История недоступна"
          description="Историю редакций видят только редакторы статьи."
          action={
            <ButtonLink to={routes.article(articleId)}>К статье</ButtonLink>
          }
        />
      )}
    </>
  );
}
