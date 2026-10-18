import clsx from 'clsx';
import styles from './Kbd.module.scss';

/** Сочетание клавиш одной плашкой: «Ctrl K». */
export function Kbd({
  keys,
  className,
}: {
  keys: string[];
  className?: string;
}) {
  return <kbd className={clsx(styles.key, className)}>{keys.join(' ')}</kbd>;
}
