import clsx from 'clsx';
import mark from './assets/dio-logo.png';
import styles from './Logo.module.scss';

/** Знак ДИО. Исходник 66×80, поэтому высота задаёт размер, ширина — по пропорции. */
export function LogoMark({
  size = 24,
  className,
}: {
  size?: number;
  className?: string;
}) {
  return (
    <img
      src={mark}
      alt=""
      aria-hidden
      className={clsx(styles.mark, className)}
      style={{ height: size }}
    />
  );
}

export function Logo({ size = 28 }: { size?: number }) {
  return (
    <span className={styles.logo}>
      <LogoMark size={size} />
      <span className={styles.word}>База знаний</span>
    </span>
  );
}
