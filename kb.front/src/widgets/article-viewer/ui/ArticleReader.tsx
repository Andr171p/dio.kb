import { useEffect, useRef, type ReactNode } from 'react';
import { useLocation } from 'react-router';
import type { ArticleDetail } from '@entities/article';
import { useUserName } from '@entities/user';
import { formatDateTime, formatRelative } from '@shared/lib/format';
import { ArticleContent } from './ArticleContent';
import { TableOfContents } from './TableOfContents';
import styles from './ArticleReader.module.scss';

interface ArticleReaderProps {
  detail: ArticleDetail;
  /** Плашки над текстом: черновик, неопубликованные изменения, архив */
  notice?: ReactNode;
  /** Бейджи статуса рядом с метаданными */
  badges?: ReactNode;
}

/** Режим чтения: заголовок, метаданные, текст статьи и оглавление справа. */
export function ArticleReader({ detail, notice, badges }: ArticleReaderProps) {
  const { article, revision } = detail;
  const contentRef = useRef<HTMLDivElement>(null);
  const author = useUserName(revision.authorId);
  const { hash } = useLocation();
  const updatedAt =
    article.publishedAt && revision.id === article.publishedRevisionId
      ? article.publishedAt
      : revision.createdAt;

  // Переход по якорю (из поиска или ссылки на раздел) — когда текст уже отрисован
  useEffect(() => {
    if (!hash) return;
    const target = document.getElementById(decodeURIComponent(hash.slice(1)));
    target?.scrollIntoView({ block: 'start' });
  }, [hash, revision.id]);

  return (
    <div className={styles.layout}>
      <article className={styles.article}>
        <header className={styles.header}>
          <h1 className={styles.title}>{revision.title}</h1>
          <div className={styles.meta}>
            {badges}
            <span>{author ?? '…'}</span>
            <span aria-hidden>·</span>
            <time dateTime={updatedAt} title={formatDateTime(updatedAt)}>
              обновлено {formatRelative(updatedAt)}
            </time>
            <span aria-hidden>·</span>
            <span>редакция {revision.number}</span>
          </div>
          {revision.summary && (
            <p className={styles.summary}>{revision.summary}</p>
          )}
        </header>
        {notice}
        <div ref={contentRef}>
          <ArticleContent markdown={revision.content} />
        </div>
      </article>
      <aside className={styles.aside}>
        <TableOfContents containerRef={contentRef} contentKey={revision.id} />
      </aside>
    </div>
  );
}
