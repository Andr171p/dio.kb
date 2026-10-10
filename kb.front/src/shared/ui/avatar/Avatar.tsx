import styles from './Avatar.module.scss';

export function Avatar({ name, size = 32 }: { name: string; size?: number }) {
  return (
    <span
      className={styles.avatar}
      style={{ width: size, height: size }}
      aria-hidden
    >
      {name.trim().charAt(0).toUpperCase() || '?'}
    </span>
  );
}
