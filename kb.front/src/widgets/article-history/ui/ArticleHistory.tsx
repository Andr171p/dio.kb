import clsx from 'clsx';
import { CircleAlert, History, RotateCcw } from 'lucide-react';
import { useMemo, useState, type ReactNode } from 'react';
import { hasPermission } from '@entities/access-grant';
import type {
  ArticleDetail,
  ArticleRevision,
  ArticleRevisionSummary,
} from '@entities/article';
import { useUserName } from '@entities/user';
import { restoreRevision } from '@features/restore-revision';
import { formatDateTime, formatRelative } from '@shared/lib/format';
import { Badge } from '@shared/ui/badge';
import { Button } from '@shared/ui/button';
import { confirmAction } from '@shared/ui/dialog';
import { EmptyState } from '@shared/ui/empty-state';
import { Notice } from '@shared/ui/notice';
import { Skeleton } from '@shared/ui/skeleton';
import { diffStats, lineDiff } from '../lib/line-diff';
import { useRevisionList, useRevisions } from '../model/revisions';
import styles from './ArticleHistory.module.scss';

type Mode = 'changes' | 'view';

function RevisionItem({
  revision,
  detail,
  selected,
  onSelect,
}: {
  revision: ArticleRevisionSummary;
  detail: ArticleDetail;
  selected: boolean;
  onSelect: () => void;
}) {
  const author = useUserName(revision.authorId);
  const current = revision.id === detail.article.currentRevisionId;
  const published = revision.id === detail.article.publishedRevisionId;

  return (
    <li>
      <button
        type="button"
        className={clsx(styles.item, selected && styles.itemSelected)}
        aria-current={selected || undefined}
        onClick={onSelect}
      >
        <span className={styles.itemHeader}>
          <span className={styles.itemNumber}>Редакция {revision.number}</span>
          {current && <Badge>текущая</Badge>}
          {published && <Badge tone="success">опубликована</Badge>}
        </span>
        <span
          className={styles.itemMeta}
          title={formatDateTime(revision.createdAt)}
        >
          {author ?? '…'} · {formatRelative(revision.createdAt)}
        </span>
        {revision.changeNote && (
          <span className={styles.itemNote}>{revision.changeNote}</span>
        )}
      </button>
    </li>
  );
}

function DiffView({
  before,
  after,
}: {
  before: ArticleRevision | null;
  after: ArticleRevision;
}) {
  const lines = useMemo(
    () =>
      lineDiff(
        before ? `# ${before.title}\n\n${before.content}` : '',
        `# ${after.title}\n\n${after.content}`,
      ),
    [before, after],
  );
  const stats = diffStats(lines);

  if (before && stats.added === 0 && stats.removed === 0)
    return (
      <p className={styles.muted}>
        Текст не отличается от предыдущей редакции.
      </p>
    );

  return (
    <div className={styles.diff}>
      <div className={styles.diffHeader}>
        <span className={styles.added}>+{stats.added}</span>
        <span className={styles.removed}>−{stats.removed}</span>
        <span className={styles.muted}>
          {before
            ? `по сравнению с редакцией ${before.number}`
            : 'первая редакция'}
        </span>
      </div>
      <div className={styles.diffBody} role="table" aria-label="Изменения">
        {lines.map((line, index) =>
          line.kind === 'skip' ? (
            <div key={index} className={styles.skip} role="row">
              ⋯ {line.count} без изменений
            </div>
          ) : (
            <div
              key={index}
              className={clsx(styles.line, styles[line.kind])}
              role="row"
            >
              <span className={styles.number}>{line.oldNumber ?? ''}</span>
              <span className={styles.number}>{line.newNumber ?? ''}</span>
              <span className={styles.sign} aria-hidden>
                {line.kind === 'added'
                  ? '+'
                  : line.kind === 'removed'
                    ? '−'
                    : ' '}
              </span>
              <span className={styles.text}>
                {line.segments.map((segment, segmentIndex) =>
                  segment.changed ? (
                    <mark key={segmentIndex} className={styles.word}>
                      {segment.text}
                    </mark>
                  ) : (
                    segment.text
                  ),
                )}
                {line.segments.every((segment) => !segment.text) && ' '}
              </span>
            </div>
          ),
        )}
      </div>
    </div>
  );
}

interface ArticleHistoryProps {
  /** Текущая (редакторская) версия статьи */
  detail: ArticleDetail;
  onRestored: (detail: ArticleDetail) => void;
  /** Рендер текста редакции — тот же, что в режиме чтения */
  renderContent: (markdown: string) => ReactNode;
}

/** История и сравнение редакций. Восстановление создаёт новую редакцию. */
export function ArticleHistory({
  detail,
  onRestored,
  renderContent,
}: ArticleHistoryProps) {
  const list = useRevisionList(
    detail.article.id,
    detail.article.currentRevisionId,
  );
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [mode, setMode] = useState<Mode>('changes');

  const revisions = list.status === 'ready' ? list.data : [];
  const selectedIndex = Math.max(
    0,
    revisions.findIndex((revision) => revision.id === selectedId),
  );
  const selected = revisions[selectedIndex];
  const previous = revisions[selectedIndex + 1];
  const contents = useRevisions(detail.article.id, [
    selected?.id,
    previous?.id,
  ]);
  const canWrite = hasPermission(detail.permissions, 'WRITE');
  const isCurrent = selected?.id === detail.article.currentRevisionId;

  if (list.status === 'error')
    return (
      <div className={styles.error}>
        <Notice>{list.error}</Notice>
      </div>
    );

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <h2 className={styles.sidebarTitle}>Редакции</h2>
        {list.status === 'loading' ? (
          <div className={styles.listSkeleton}>
            {[0, 1, 2].map((index) => (
              <Skeleton key={index} height={56} />
            ))}
          </div>
        ) : (
          <ul className={styles.list}>
            {revisions.map((revision) => (
              <RevisionItem
                key={revision.id}
                revision={revision}
                detail={detail}
                selected={revision.id === selected?.id}
                onSelect={() => setSelectedId(revision.id)}
              />
            ))}
          </ul>
        )}
      </aside>

      <section className={styles.main}>
        {!selected ? (
          list.status === 'ready' && (
            <EmptyState icon={History} title="Редакций пока нет" />
          )
        ) : (
          <>
            <header className={styles.header}>
              <div className={styles.headerText}>
                <h2 className={styles.title}>Редакция {selected.number}</h2>
                <p className={styles.muted}>
                  {formatDateTime(selected.createdAt)}
                </p>
              </div>
              <div
                className={styles.segmented}
                role="tablist"
                aria-label="Режим"
              >
                {(['changes', 'view'] as const).map((value) => (
                  <button
                    key={value}
                    type="button"
                    role="tab"
                    aria-selected={mode === value}
                    className={clsx(
                      styles.segment,
                      mode === value && styles.segmentActive,
                    )}
                    onClick={() => setMode(value)}
                  >
                    {value === 'changes' ? 'Изменения' : 'Просмотр'}
                  </button>
                ))}
              </div>
              {canWrite &&
                !isCurrent &&
                detail.article.status !== 'archived' && (
                  <Button
                    size="sm"
                    icon={RotateCcw}
                    onClick={() =>
                      confirmAction({
                        title: `Восстановить редакцию ${selected.number}?`,
                        description:
                          'Будет создана новая редакция с этим содержимым. История сохранится, опубликованная версия не изменится до публикации.',
                        confirmLabel: 'Восстановить',
                        onConfirm: async () => {
                          const restored = await restoreRevision(
                            detail.article,
                            selected,
                          );
                          if (restored) {
                            setSelectedId(null);
                            onRestored(restored);
                          }
                        },
                      })
                    }
                  >
                    Восстановить
                  </Button>
                )}
            </header>

            {contents.status === 'loading' && (
              <div className={styles.listSkeleton}>
                <Skeleton height={14} width="80%" />
                <Skeleton height={14} width="60%" />
                <Skeleton height={14} width="70%" />
              </div>
            )}
            {contents.status === 'error' && (
              <Notice>
                <CircleAlert size={14} aria-hidden /> {contents.error}
              </Notice>
            )}
            {contents.status === 'ready' &&
              contents.data[0] &&
              (mode === 'changes' ? (
                <DiffView before={contents.data[1]} after={contents.data[0]} />
              ) : (
                <article className={styles.preview}>
                  <h1 className={styles.previewTitle}>
                    {contents.data[0].title}
                  </h1>
                  {renderContent(contents.data[0].content)}
                </article>
              ))}
          </>
        )}
      </section>
    </div>
  );
}
