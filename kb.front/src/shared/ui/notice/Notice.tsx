import clsx from 'clsx';
import { CircleAlert } from 'lucide-react';
import type { ReactNode } from 'react';
import styles from './Notice.module.scss';

interface NoticeProps {
  children: ReactNode;
  action?: ReactNode;
  className?: string;
}

/** Сообщение об ошибке. Цвет всегда сопровождается иконкой и текстом. */
export function Notice({ children, action, className }: NoticeProps) {
  return (
    <div role="alert" className={clsx(styles.notice, className)}>
      <CircleAlert size={16} className={styles.icon} aria-hidden />
      <div className={styles.text}>{children}</div>
      {action}
    </div>
  );
}
