import styles from './Logo.module.scss';

export function LogoMark({ size = 24 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      aria-hidden
      className={styles.mark}
    >
      <path
        fill="#bb252d"
        d="M3 21V11.5A8.5 8.5 0 0 1 11.5 3H15v5.5h-3.5a3 3 0 0 0-3 3V21Z"
      />
      <path
        fill="#9a9a96"
        d="M15.5 9H21v6a7 7 0 0 1-7 7H9v-5.5h5a1.5 1.5 0 0 0 1.5-1.5Z"
      />
      <circle cx="19.5" cy="4.5" r="1.8" fill="#b5b5b0" />
    </svg>
  );
}

export function Logo() {
  return (
    <span className={styles.logo} aria-label="DIOS Knowledge">
      <LogoMark size={22} />
      <span className={styles.word}>DIOS</span>
      <span className={styles.suffix}>knowledge</span>
    </span>
  );
}
