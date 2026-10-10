import clsx from 'clsx';
import { X } from 'lucide-react';
import { useEffect, useId, useRef, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { IconButton } from '../button';
import styles from './Dialog.module.scss';

interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: ReactNode;
  size?: 'sm' | 'md';
  children: ReactNode;
}

/**
 * Модальное окно на нативном <dialog>: фокус-ловушка, Esc и top layer из коробки.
 * Рендерится в body, поэтому его можно вызывать из любого места разметки, например из абзаца.
 */
export function Dialog({
  open,
  onClose,
  title,
  description,
  size = 'sm',
  children,
}: DialogProps) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;

    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return createPortal(
    <dialog
      ref={ref}
      className={clsx(styles.dialog, styles[size])}
      aria-labelledby={titleId}
      onClose={onClose}
      onClick={(event) => {
        // Клик по подложке
        if (event.target === event.currentTarget) onClose();
      }}
    >
      {open && (
        <div className={styles.content}>
          <header className={styles.header}>
            <h2 id={titleId} className={styles.title}>
              {title}
            </h2>
            {description && <p className={styles.description}>{description}</p>}
          </header>
          {children}
          {/* В конце DOM: showModal фокусирует первый элемент, и им должно быть поле формы */}
          <IconButton
            icon={X}
            label="Закрыть"
            tooltip={false}
            className={styles.close}
            onClick={onClose}
          />
        </div>
      )}
    </dialog>,
    document.body,
  );
}

export function DialogActions({ children }: { children: ReactNode }) {
  return <div className={styles.actions}>{children}</div>;
}
