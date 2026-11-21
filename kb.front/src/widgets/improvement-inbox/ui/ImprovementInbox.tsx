import clsx from 'clsx';
import { CircleHelp, Sparkles } from 'lucide-react';
import { Link } from 'react-router';
import {
  GAP_KIND_ACTION,
  GAP_KIND_LABELS,
  GAP_STATUS_LABELS,
  type GapStatus,
  type KnowledgeGap,
} from '@entities/knowledge-gap';
import type { Space } from '@entities/space';
import { routes } from '@shared/config/routes';
import { EmptyState } from '@shared/ui/empty-state';
import { Notice } from '@shared/ui/notice';
import { Skeleton } from '@shared/ui/skeleton';
import styles from './ImprovementInbox.module.scss';

interface ImprovementInboxProps {
  items: KnowledgeGap[];
  spaces: Space[];
  status: 'loading' | 'ready' | 'error';
  error?: string | null;
  filter: GapStatus | 'all';
  onFilter: (status: GapStatus | 'all') => void;
  totals: Partial<Record<GapStatus, number>>;
}

const FILTERS: { value: GapStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'Все' },
  { value: 'open', label: 'Ожидают разбора' },
  { value: 'in_progress', label: 'В работе' },
  { value: 'resolved', label: 'Решены' },
  { value: 'dismissed', label: 'Отклонены' },
];

export function ImprovementInbox({
  items,
  spaces,
  status,
  error,
  filter,
  onFilter,
  totals,
}: ImprovementInboxProps) {
  const spaceName = (id: string | null) =>
    id ? (spaces.find((space) => space.id === id)?.name ?? 'Пространство') : 'Организация';

  return (
    <div className={styles.root}>
      <div className={styles.totals} role="group" aria-label="Статусы">
        {FILTERS.filter((item) => item.value !== 'all' && item.value !== 'dismissed').map(
          (item) => (
            <button
              key={item.value}
              type="button"
              className={clsx(
                styles.total,
                filter === item.value && styles.totalActive,
              )}
              onClick={() => onFilter(item.value)}
            >
              <span className={styles.totalLabel}>{item.label}</span>
              <span className={styles.totalValue}>
                {totals[item.value as GapStatus] ?? 0}
              </span>
            </button>
          ),
        )}
      </div>

      <div className={styles.filters} role="group" aria-label="Фильтр">
        {FILTERS.map((item) => (
          <button
            key={item.value}
            type="button"
            aria-pressed={filter === item.value}
            className={clsx(styles.chip, filter === item.value && styles.chipActive)}
            onClick={() => onFilter(item.value)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {status === 'error' && <Notice>{error}</Notice>}

      {status === 'loading' && items.length === 0 && (
        <div className={styles.skeletons}>
          {[0, 1, 2].map((index) => (
            <Skeleton key={index} height={88} />
          ))}
        </div>
      )}

      {status === 'ready' && items.length === 0 && (
        <EmptyState
          icon={Sparkles}
          title="Пока нет улучшений"
          description="Сигналы появятся после оценок AI-ответов и проблем в поиске. Backend сам группирует повторяющиеся вопросы."
        />
      )}

      <ul className={styles.list}>
        {items.map((gap) => (
          <li key={gap.id}>
            <Link
              to={routes.knowledgeImprovements(gap.id)}
              className={styles.card}
            >
              <span className={styles.cardTitle}>{gap.title}</span>
              <span className={styles.cardMeta}>
                {GAP_KIND_LABELS[gap.kind]}
                <span aria-hidden>·</span>
                {gap.signalCount} сигнал
                {gap.signalCount === 1 ? '' : gap.signalCount < 5 ? 'а' : 'ов'}
                <span aria-hidden>·</span>
                {spaceName(gap.spaceId)}
                <span aria-hidden>·</span>
                {GAP_STATUS_LABELS[gap.status]}
              </span>
              <span className={styles.cardAction}>
                <CircleHelp size={14} aria-hidden />
                Рекомендация: {GAP_KIND_ACTION[gap.kind]}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
