import clsx from 'clsx';
import type { LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';
import styles from './Callout.module.scss';

interface CalloutProps {
  icon?: LucideIcon;
  tone?: 'info' | 'warning' | 'neutral';
  title?: ReactNode;
  children?: ReactNode;
  actions?: ReactNode;
  className?: string;
}

/** Плашка состояния над содержимым: черновик, неопубликованные изменения, архив. */
export function Callout({
  icon: Icon,
  tone = 'neutral',
  title,
  children,
  actions,
  className,
}: CalloutProps) {
  return (
    <div
      className={clsx(styles.callout, styles[tone], className)}
      role="status"
    >
      {Icon && <Icon size={18} className={styles.icon} aria-hidden />}
      <div className={styles.text}>
        {title && <p className={styles.title}>{title}</p>}
        {children && <p className={styles.body}>{children}</p>}
      </div>
      {actions && <div className={styles.actions}>{actions}</div>}
    </div>
  );
}
