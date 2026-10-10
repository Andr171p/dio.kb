import clsx from 'clsx';
import styles from './Skeleton.module.scss';

interface SkeletonProps {
  width?: number | string;
  height?: number | string;
  className?: string;
}

export function Skeleton({
  width = '100%',
  height = 14,
  className,
}: SkeletonProps) {
  return (
    <span
      className={clsx(styles.skeleton, className)}
      style={{ width, height }}
      aria-hidden
    />
  );
}
