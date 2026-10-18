import clsx from 'clsx';
import type { LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';
import styles from './EmptyState.module.scss';

interface EmptyStateProps {
  /** Иконка для контекстов без заголовка; в карточке состояния не показывается */
  icon?: LucideIcon;
  tone?: 'default' | 'warning';
  title: string;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({
  icon: Icon,
  tone = 'default',
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={clsx(
        styles.empty,
        tone === 'warning' && styles.warning,
        className,
      )}
    >
      {Icon && (
        <span className={styles.icon}>
          <Icon size={20} aria-hidden />
        </span>
      )}
      <p className={styles.title}>{title}</p>
      {description && <p className={styles.description}>{description}</p>}
      {action && <div className={styles.action}>{action}</div>}
    </div>
  );
}
