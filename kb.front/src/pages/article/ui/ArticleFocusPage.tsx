import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router';
import { loadSpaces, useSpace } from '@entities/space';
import { ArticleReader } from '@widgets/article-viewer';
import { routes } from '@shared/config/routes';
import { Breadcrumbs } from '@shared/ui/breadcrumbs';
import { ButtonLink } from '@shared/ui/button';
import { EmptyState } from '@shared/ui/empty-state';
import { Skeleton } from '@shared/ui/skeleton';
import { useArticleForReading } from '../model/use-article-for-reading';
import styles from './ArticleFocusPage.module.scss';

/** Режим фокуса: только текст статьи, без навигации. Esc — выход. */
export function ArticleFocusPage() {
  const { articleId = '' } = useParams();
  const navigate = useNavigate();
  const result = useArticleForReading(articleId, 'published');
  const detail = result.status === 'ready' ? result.detail : null;
  const space = useSpace(detail?.article.spaceId);

  useEffect(() => {
    void loadSpaces();
  }, []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      // Esc сначала закрывает открытые окна и панели, а не режим фокуса
      if (event.key !== 'Escape' || event.defaultPrevented) return;
      if (document.querySelector('dialog[open], :popover-open')) return;
      void navigate(routes.article(articleId));
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [navigate, articleId]);

  return (
    <>
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <Breadcrumbs
            className={styles.crumbs}
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
            ]}
          />
          <ButtonLink to={routes.article(articleId)} className={styles.exit}>
            Выйти из режима фокуса
          </ButtonLink>
        </div>
      </header>

      {result.status === 'loading' && (
        <div className={styles.loading}>
          <Skeleton height={44} width="70%" />
          <Skeleton height={14} width="40%" />
          <Skeleton height={140} />
        </div>
      )}
      {result.status === 'missing' && (
        <div className={styles.loading}>
          <EmptyState
            title="Статья недоступна"
            description="Возможно, её сняли с публикации или у вас нет доступа."
            action={<ButtonLink to={routes.home()}>На главную</ButtonLink>}
          />
        </div>
      )}
      {detail && (
        <ArticleReader
          key={detail.revision.id}
          detail={detail}
          variant="focus"
        />
      )}
    </>
  );
}
