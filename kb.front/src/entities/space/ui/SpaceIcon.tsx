import clsx from 'clsx';
import type { CSSProperties } from 'react';
import styles from './SpaceIcon.module.scss';

const HUES = [356, 24, 42, 150, 190, 215, 262, 300];

function hueFor(key: string): number {
  let hash = 0;
  for (const char of key) hash = (hash * 31 + char.charCodeAt(0)) | 0;
  return HUES[Math.abs(hash) % HUES.length];
}

interface SpaceIconProps {
  spaceKey: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

/** Иконка пространства: первые буквы ключа на стабильном по ключу цвете. */
export function SpaceIcon({
  spaceKey,
  size = 'sm',
  className,
}: SpaceIconProps) {
  return (
    <span
      className={clsx(styles.icon, styles[size], className)}
      style={{ '--space-hue': hueFor(spaceKey) } as CSSProperties}
      aria-hidden
    >
      {spaceKey.replace(/[^A-Z0-9]/g, '').slice(0, 2) || '?'}
    </span>
  );
}
