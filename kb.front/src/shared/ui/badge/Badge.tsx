import clsx from 'clsx';
import type { ReactNode } from 'react';
import styles from './Badge.module.scss';

interface BadgeProps {
  tone?: 'neutral' | 'success' | 'accent' | 'warning' | 'info';
  className?: string;
  children: ReactNode;
}

export function Badge({ tone = 'neutral', className, children }: BadgeProps) {
  return (
    <span className={clsx(styles.badge, styles[tone], className)}>
      {children}
    </span>
  );
}
