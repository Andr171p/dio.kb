import clsx from 'clsx';
import { ArrowUpRight } from 'lucide-react';
import { useEffect, useMemo, useRef, type ReactNode } from 'react';
import { Link, useLocation } from 'react-router';
import type { ArticleDetail } from '@entities/article';
import { useUserName } from '@entities/user';
import {
  ReadingSettingsButton,
  TextSizeControl,
  useReadingStyle,
} from '@features/reading-settings';
import { SelectionSearch } from '@features/selection-search';
import { routes } from '@shared/config/routes';
import { formatDateTime, formatShortDate, pluralize } from '@shared/lib/format';
import { useScrollProgress } from '@shared/lib/hooks';
import { ButtonLink } from '@shared/ui/button';
import { readingMinutes, relatedArticles } from '../lib/reading';
import { useActiveHeading, useHeadings } from '../model/headings';
import { ArticleContent } from './ArticleContent';
import { TableOfContents, TableOfContentsMenu } from './TableOfContents';
import styles from './ArticleReader.module.scss';

const SUMMARY_ID = 'summary';

interface ArticleReaderProps {
  detail: ArticleDetail;
  /** Режим фокуса: одна колонка крупнее, без правой панели */
  variant?: 'default' | 'focus';
  /** Строка пути над заголовком: «1С и учёт / Администрирование» */
  eyebrow?: string;
  /** Статус рядом со временем чтения */
  status?: ReactNode;
  /** Плашки над текстом: черновик, неопубликованные изменения, архив */
  notice?: ReactNode;
  /** Чеклисты можно отмечать (только при чтении, не в предпросмотре) */
  interactive?: boolean;
}

/** Режим чтения: заголовок, метаданные, «Коротко», текст и правая колонка. */
export function ArticleReader({
  detail,
  variant = 'default',
  eyebrow,
  status,
  notice,
  interactive = true,
}: ArticleReaderProps) {
  const { article, revision } = detail;
  const focus = variant === 'focus';
  const articleRef = useRef<HTMLElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const author = useUserName(revision.authorId);
  const { hash } = useLocation();
  const readingStyle = useReadingStyle(focus ? 1 : 0);
  const progress = useScrollProgress(articleRef);
  const updatedAt =
    article.publishedAt && revision.id === article.publishedRevisionId
      ? article.publishedAt
      : revision.createdAt;
  const minutes = useMemo(
    () => readingMinutes(revision.content),
    [revision.content],
  );
  const related = useMemo(
    () => relatedArticles(revision.content, article.id),
    [revision.content, article.id],
  );
  const headings = useHeadings(
    contentRef,
    revision.id,
    revision.summary ? [{ id: SUMMARY_ID, text: 'Коротко', level: 2 }] : [],
  );
  const active = useActiveHeading(headings);
  const readingTime = `${pluralize(minutes, ['минута', 'минуты', 'минут'])} чтения`;

  // Переход по якорю (из поиска или ссылки на раздел) — когда текст уже отрисован
  useEffect(() => {
    if (!hash) return;
    const target = document.getElementById(decodeURIComponent(hash.slice(1)));
    target?.scrollIntoView({ block: 'start' });
  }, [hash, revision.id]);

  return (
    <div
      className={clsx(styles.layout, focus && styles.focus)}
      style={readingStyle}
    >
      <article ref={articleRef} className={styles.article}>
        <header className={styles.header}>
          {eyebrow && !focus && <p className={styles.eyebrow}>{eyebrow}</p>}
          <h1 className={styles.title}>{revision.title}</h1>
          <p className={styles.meta}>
            <span className={styles.hideMobile}>{author ?? '…'} · </span>
            {focus ? (
              <>
                Редакция {revision.number} · {readingTime}
              </>
            ) : (
              <>
                <time dateTime={updatedAt} title={formatDateTime(updatedAt)}>
                  <span className={styles.hideMobile}>Обновлено </span>
                  {formatShortDate(updatedAt)}
                </time>{' '}
                · Редакция {revision.number}
              </>
            )}
          </p>
          {!focus && (
            <div className={styles.status}>
              {status}
              <span>{readingTime}</span>
            </div>
          )}
        </header>

        {!focus && (
          <div className={styles.mobileToc}>
            <TableOfContentsMenu headings={headings} active={active} />
          </div>
        )}

        {notice && <div className={styles.notice}>{notice}</div>}

        {revision.summary && (
          <section
            id={SUMMARY_ID}
            className={styles.summary}
            aria-label="Коротко"
          >
            <p className={styles.summaryLabel}>Коротко</p>
            <p className={styles.summaryText}>{revision.summary}</p>
          </section>
        )}

        <div ref={contentRef} className={styles.content}>
          <ArticleContent
            markdown={revision.content}
            checklistKey={interactive ? revision.id : undefined}
          />
        </div>
        {interactive && (
          <SelectionSearch containerRef={contentRef} articleId={article.id} />
        )}
      </article>

      {!focus && (
        <aside className={styles.rail}>
          <TableOfContents headings={headings} active={active} />
          {related.length > 0 && (
            <section className={styles.related}>
              <h2 className={styles.relatedTitle}>Связанные материалы</h2>
              <ul className={styles.relatedList}>
                {related.map((item) => (
                  <li key={item.id}>
                    <Link
                      to={routes.article(item.id)}
                      className={styles.relatedLink}
                    >
                      {item.title}
                      <ArrowUpRight size={13} aria-hidden />
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </aside>
      )}

      {focus ? (
        <footer className={styles.focusFooter}>
          <div className={styles.focusFooterInner}>
            <span className={styles.progress}>Прочитано {progress}%</span>
            <TextSizeControl compact offset={1} />
          </div>
        </footer>
      ) : (
        <footer className={styles.mobileBar}>
          <span className={styles.progress}>{progress}% прочитано</span>
          <ReadingSettingsButton compact />
          <ButtonLink
            to={routes.articleFocus(article.id)}
            variant="ghost"
            size="sm"
          >
            Фокус
          </ButtonLink>
        </footer>
      )}
    </div>
  );
}
