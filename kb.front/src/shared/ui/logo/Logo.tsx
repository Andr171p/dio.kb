import styles from './Logo.module.scss';

const DIOS_MARK = '/brand/dios-mark.png';
const KNOWLEDGE_MARK = '/brand/knowledge-mark.png';

export function LogoMark({ size = 24 }: { size?: number }) {
  return (
    <img
      src={DIOS_MARK}
      alt=""
      width={size}
      height={size}
      className={styles.mark}
      draggable={false}
    />
  );
}

/** Марка Knowledge / «Ответ от ИИ» — спокойный синий знак вместо красного акцента. */
export function KnowledgeMark({ size = 22 }: { size?: number }) {
  return (
    <img
      src={KNOWLEDGE_MARK}
      alt=""
      width={size}
      height={size}
      className={styles.knowledgeMark}
      draggable={false}
    />
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
