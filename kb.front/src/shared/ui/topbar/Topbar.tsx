import clsx from 'clsx';
import type { ReactNode } from 'react';
import styles from './Topbar.module.scss';

interface TopbarProps {
  start?: ReactNode;
  end?: ReactNode;
  className?: string;
}

/** Липкая верхняя панель страницы: хлебные крошки слева, действия справа. */
export function Topbar({ start, end, className }: TopbarProps) {
  return (
    <header className={clsx(styles.topbar, className)}>
      <div className={styles.start}>{start}</div>
      {end && <div className={styles.end}>{end}</div>}
    </header>
  );
}
