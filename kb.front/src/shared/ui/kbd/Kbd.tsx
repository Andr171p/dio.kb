import styles from './Kbd.module.scss';

export function Kbd({ keys }: { keys: string[] }) {
  return (
    <span className={styles.combo}>
      {keys.map((key) => (
        <kbd key={key} className={styles.key}>
          {key}
        </kbd>
      ))}
    </span>
  );
}
