import clsx from 'clsx';
import { FileText, Globe, Ticket } from 'lucide-react';
import { useState } from 'react';
import type { LinkPreview } from '../model/types';
import styles from './LinkPreviewCard.module.scss';

const ARTICLE_STATUS_LABELS = {
  draft: 'черновик',
  published: 'опубликована',
  archived: 'в архиве',
} as const;

const TICKET_STATUS_LABELS: Record<string, string> = {
  new: 'Новая',
  pending_approval: 'На согласовании',
  open: 'Открыта',
  in_progress: 'В работе',
  waiting: 'Ожидание',
  paused: 'Приостановлена',
  resolved: 'Решена',
  closed: 'Закрыта',
  reopened: 'Переоткрыта',
  rejected: 'Отклонена',
  canceled: 'Отменена',
};

function hostname(href: string): string {
  try {
    return new URL(href, window.location.origin).hostname;
  } catch {
    return href;
  }
}

interface LinkPreviewBodyProps {
  href: string;
  /** undefined — загружается, null — превью недоступно */
  preview: LinkPreview | null | undefined;
  compact?: boolean;
}

/** Содержимое карточки ссылки: общее для карточки в тексте и всплывающего превью. */
export function LinkPreviewBody({
  href,
  preview,
  compact,
}: LinkPreviewBodyProps) {
  const [imageFailed, setImageFailed] = useState(false);

  if (preview === undefined) {
    return (
      <div className={styles.body} aria-busy>
        <span className={clsx(styles.skeleton, styles.skeletonMeta)} />
        <span className={clsx(styles.skeleton, styles.skeletonTitle)} />
        {!compact && (
          <span className={clsx(styles.skeleton, styles.skeletonText)} />
        )}
      </div>
    );
  }

  if (preview === null) {
    return (
      <div className={styles.body}>
        <span className={styles.meta}>
          <Globe size={13} aria-hidden />
          {hostname(href)}
        </span>
        <span className={clsx(styles.title, styles.url)}>{href}</span>
      </div>
    );
  }

  if (preview.kind === 'article') {
    return (
      <div className={styles.body}>
        <span className={styles.meta}>
          <FileText size={13} aria-hidden />
          Статья базы знаний · {ARTICLE_STATUS_LABELS[preview.status]}
        </span>
        <span className={styles.title}>{preview.title}</span>
        {preview.summary && (
          <span className={styles.text}>{preview.summary}</span>
        )}
      </div>
    );
  }

  if (preview.kind === 'ticket') {
    return (
      <div className={styles.body}>
        <span className={styles.meta}>
          <Ticket size={13} aria-hidden />
          Заявка DIOS · {TICKET_STATUS_LABELS[preview.status] ?? preview.status}
        </span>
        <span className={styles.title}>
          <span className={styles.number}>{preview.number}</span>{' '}
          {preview.title}
        </span>
      </div>
    );
  }

  const showImage = !compact && preview.imageUrl && !imageFailed;
  return (
    <div className={clsx(styles.body, showImage && styles.withImage)}>
      <div className={styles.columns}>
        <div className={styles.textColumn}>
          <span className={styles.meta}>
            {preview.faviconUrl ? (
              <img
                className={styles.favicon}
                src={preview.faviconUrl}
                alt=""
                referrerPolicy="no-referrer"
                onError={(event) => (event.currentTarget.hidden = true)}
              />
            ) : (
              <Globe size={13} aria-hidden />
            )}
            {preview.siteName ?? hostname(href)}
          </span>
          <span className={styles.title}>{preview.title ?? href}</span>
          {preview.description && (
            <span className={styles.text}>{preview.description}</span>
          )}
        </div>
        {showImage && (
          <img
            className={styles.image}
            src={preview.imageUrl ?? undefined}
            alt=""
            loading="lazy"
            referrerPolicy="no-referrer"
            onError={() => setImageFailed(true)}
          />
        )}
      </div>
    </div>
  );
}
