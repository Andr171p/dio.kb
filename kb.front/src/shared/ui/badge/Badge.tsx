import clsx from 'clsx';
import type { ReactNode } from 'react';
import styles from './Badge.module.scss';

interface BadgeProps {
  tone?: 'neutral' | 'success' | 'accent' | 'warning' | 'info';
  size?: 'md' | 'sm';
  className?: string;
  children: ReactNode;
}

export function Badge({
  tone = 'neutral',
  size = 'md',
  className,
  children,
}: BadgeProps) {
  return (
    <span
      className={clsx(
        styles.badge,
        styles[tone],
        size === 'sm' && styles.sm,
        className,
      )}
    >
      {children}
    </span>
  );
}
