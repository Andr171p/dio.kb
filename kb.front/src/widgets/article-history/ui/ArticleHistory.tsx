import clsx from 'clsx';
import { useMemo, useState, type ReactNode } from 'react';
import { hasPermission } from '@entities/access-grant';
import type {
  ArticleDetail,
  ArticleRevision,
  ArticleRevisionSummary,
} from '@entities/article';
import { useUserName } from '@entities/user';
import { restoreRevision } from '@features/restore-revision';
import {
  formatDateTime,
  formatDayTime,
  formatShortDate,
} from '@shared/lib/format';
import { Button } from '@shared/ui/button';
import { Chip, ChipGroup } from '@shared/ui/chip';
import { confirmAction } from '@shared/ui/dialog';
import { EmptyState } from '@shared/ui/empty-state';
import { Notice } from '@shared/ui/notice';
import { Skeleton } from '@shared/ui/skeleton';
import { lineDiff, type DiffLine } from '../lib/line-diff';
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
        <span className={styles.itemNumber}>Редакция {revision.number}</span>
        <span
          className={clsx(styles.itemMeta, published && styles.itemPublished)}
          title={formatDateTime(revision.createdAt)}
        >
          {published
            ? 'Опубликована'
            : current
              ? 'Текущий черновик'
              : formatDayTime(revision.createdAt)}
        </span>
        {revision.changeNote && (
          <span className={styles.itemNote}>{revision.changeNote}</span>
        )}
      </button>
    </li>
  );
}

type DiffBlock =
  | { kind: 'added' | 'removed' | 'same'; lines: DiffLine[] }
  | { kind: 'skip'; count: number };

/** Соседние строки одного вида — один блок: «удалено» красным, «добавлено» зелёным. */
function groupLines(lines: DiffLine[]): DiffBlock[] {
  const blocks: DiffBlock[] = [];
  for (const line of lines) {
    if (line.kind === 'skip') {
      blocks.push({ kind: 'skip', count: line.count });
      continue;
    }
    const last = blocks.at(-1);
    if (last && last.kind === line.kind) last.lines.push(line);
    else blocks.push({ kind: line.kind, lines: [line] });
  }
  return blocks;
}

const SIGNS = { added: '+', removed: '−', same: ' ' } as const;

function DiffView({
  before,
  after,
}: {
  before: ArticleRevision | null;
  after: ArticleRevision;
}) {
  const blocks = useMemo(
    () =>
      groupLines(
        lineDiff(
          before ? `# ${before.title}\n\n${before.content}` : '',
          `# ${after.title}\n\n${after.content}`,
        ),
      ),
    [before, after],
  );
  const unchanged = blocks.every(
    (block) => block.kind === 'same' || block.kind === 'skip',
  );

  return (
    <div className={styles.diff}>
      <p className={styles.compare}>
        {before
          ? `По сравнению с редакцией ${before.number}`
          : 'Первая редакция статьи'}
      </p>
      {before && unchanged ? (
        <p className={styles.compare}>
          Текст не отличается от предыдущей редакции.
        </p>
      ) : (
        <div className={styles.blocks} role="table" aria-label="Изменения">
          {blocks.map((block, index) =>
            block.kind === 'skip' ? (
              <div key={index} className={styles.skip} role="row">
                ⋯ без изменений: {block.count}
              </div>
            ) : (
              <div
                key={index}
                className={clsx(styles.block, styles[block.kind])}
              >
                {block.lines.map(
                  (line, lineIndex) =>
                    line.kind !== 'skip' && (
                      <div key={lineIndex} className={styles.line} role="row">
                        <span className={styles.sign} aria-hidden>
                          {SIGNS[line.kind]}
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
                          {line.segments.every((segment) => !segment.text) &&
                            ' '}
                        </span>
                      </div>
                    ),
                )}
              </div>
            ),
          )}
        </div>
      )}
    </div>
  );
}

function RevisionAuthor({ authorId }: { authorId: string }) {
  return <>{useUserName(authorId) ?? '…'}</>;
}

interface ArticleHistoryProps {
  /** Текущая (редакторская) версия статьи */
  detail: ArticleDetail;
  onRestored: (detail: ArticleDetail) => void;
  /** Рендер текста редакции — тот же, что в режиме чтения */
  renderContent: (markdown: string) => ReactNode;
  /** Действие справа под сравнением, например «Вернуться к статье» */
  aside?: ReactNode;
}

/** История и сравнение редакций. Восстановление создаёт новую редакцию. */
export function ArticleHistory({
  detail,
  onRestored,
  renderContent,
  aside,
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
  const canRestore =
    canWrite && !isCurrent && detail.article.status !== 'archived';

  if (list.status === 'error') return <Notice>{list.error}</Notice>;

  const restore = () => {
    if (!selected) return;
    confirmAction({
      title: `Восстановить редакцию ${selected.number}?`,
      description:
        'Будет создан новый черновик с этим содержимым. История сохранится, опубликованная версия останется прежней.',
      confirmLabel: 'Восстановить',
      onConfirm: async () => {
        const restored = await restoreRevision(detail.article, selected);
        if (restored) {
          setSelectedId(null);
          onRestored(restored);
        }
      },
    });
  };

  return (
    <div className={styles.layout}>
      <nav className={styles.sidebar} aria-label="Редакции">
        {list.status === 'loading' ? (
          <div className={styles.listSkeleton}>
            {[0, 1, 2].map((index) => (
              <Skeleton key={index} height={64} />
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
      </nav>

      <section className={styles.main}>
        {!selected ? (
          list.status === 'ready' && <EmptyState title="Редакций пока нет" />
        ) : (
          <>
            <header className={styles.header}>
              <h2 className={styles.title}>Редакция {selected.number}</h2>
              <p
                className={styles.meta}
                title={formatDateTime(selected.createdAt)}
              >
                {formatShortDate(selected.createdAt)} ·{' '}
                <RevisionAuthor authorId={selected.authorId} />
              </p>
              <ChipGroup className={styles.modes} aria-label="Режим">
                <Chip
                  selected={mode === 'changes'}
                  onClick={() => setMode('changes')}
                >
                  Изменения
                </Chip>
                <Chip
                  selected={mode === 'view'}
                  onClick={() => setMode('view')}
                >
                  Просмотр
                </Chip>
              </ChipGroup>
            </header>

            {contents.status === 'loading' && (
              <div className={styles.listSkeleton}>
                <Skeleton height={54} />
                <Skeleton height={90} />
              </div>
            )}
            {contents.status === 'error' && <Notice>{contents.error}</Notice>}
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

            {canRestore && (
              <p className={styles.restoreHint}>
                Восстановление создаст новый черновик.
                <br />
                Опубликованная версия останется прежней.
              </p>
            )}
            <div className={styles.actions}>
              {canRestore && (
                <Button className={styles.restore} onClick={restore}>
                  Восстановить редакцию
                </Button>
              )}
              {aside && <div className={styles.aside}>{aside}</div>}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
